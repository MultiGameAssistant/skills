#!/usr/bin/env node
/**
 * 技能库的检查：index.json 和每个 SKILL.md 对得上，每个技能有版本号；
 * 给了一个 git 提交（上一个版本）时，再查改过文件的技能升了版本号。
 *
 * 用法:
 *   node .github/scripts/check.mjs              # 只查格式
 *   node .github/scripts/check.mjs HEAD~1       # 再和上一个提交比版本号
 */
import { execFileSync } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

const NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
const VERSION = /^\d+\.\d+\.\d+$/
const REQUIRES = /^(>=|>|<=|<|\^|=)?\s*v?\d[\w.]*(\s+(>=|>|<=|<|\^|=)?\s*v?\d[\w.]*)*$/
const errors = []
const fail = message => errors.push(message)

function frontmatter(text) {
  const match = /^﻿?---\r?\n([\s\S]*?)\r?\n---/.exec(text)
  if (match === null) return undefined
  const field = key => new RegExp(`^${key}:\\s*(.+)$`, 'm').exec(match[1])?.[1]?.trim().replace(/^"(.*)"$/, '$1')
  return { name: field('name'), description: field('description') }
}

function compare(a, b) {
  const x = a.split('.').map(Number)
  const y = b.split('.').map(Number)
  for (let i = 0; i < 3; i++) if (x[i] !== y[i]) return Math.sign(x[i] - y[i])
  return 0
}

const index = JSON.parse(readFileSync('index.json', 'utf8').replace(/^﻿/, ''))
const seen = new Set()
for (const skill of index.skills ?? []) {
  const where = `index.json「${skill.name ?? '?'}」`
  if (!NAME.test(skill.name ?? '')) fail(`${where}：name 要用小写字母、数字、短横线`)
  if (seen.has(skill.name)) fail(`${where}：重名`)
  seen.add(skill.name)
  if (typeof skill.path !== 'string' || skill.path.includes('..')) { fail(`${where}：path 不对`); continue }
  const file = join(skill.path, 'SKILL.md')
  if (!existsSync(file)) { fail(`${where}：${file} 不存在`); continue }
  const front = frontmatter(readFileSync(file, 'utf8'))
  if (front === undefined) fail(`${file}：开头没有 --- frontmatter ---`)
  else {
    if (front.name !== undefined && front.name !== skill.name) fail(`${file}：frontmatter 的 name（${front.name}）和 index.json 的（${skill.name}）不一样`)
    if (!front.description) fail(`${file}：没有 description`)
  }
  if (!VERSION.test(skill.version ?? '')) fail(`${where}：version 要写成 主.次.修订（例如 1.0.0）`)
  if (skill.requires !== undefined && !REQUIRES.test(skill.requires)) fail(`${where}：requires 写法不对（例如 >=2.1.0）`)
  if (skill.changes !== undefined && skill.changes.length > 300) fail(`${where}：changes 写一句就够（300 字以内）`)
  if (skill.kind !== undefined && !['game', 'script', 'general'].includes(skill.kind)) fail(`${where}：kind 只能是 game、script、general`)
}

// 和上一个版本比：改了文件夹里任何文件的技能，版本号要比原来大。
const base = process.argv[2]
if (base !== undefined && base !== '' && !/^0+$/.test(base)) {
  const git = (...args) => execFileSync('git', args, { encoding: 'utf8' })
  let before
  try {
    before = JSON.parse(git('show', `${base}:index.json`).replace(/^﻿/, ''))
  } catch {
    before = { skills: [] }
  }
  const changed = git('diff', '--name-only', base).split('\n').filter(Boolean)
  for (const skill of index.skills ?? []) {
    if (typeof skill.path !== 'string') continue
    const old = before.skills?.find(s => s.name === skill.name)
    const touched = changed.some(f => f.startsWith(`${skill.path}/`))
    if (old === undefined || !touched) continue
    if (!VERSION.test(old.version ?? '')) continue // 上一版还没有版本号
    if (!VERSION.test(skill.version ?? '') || compare(skill.version, old.version) <= 0) {
      fail(`「${skill.name}」改了文件，version 要比原来的 ${old.version} 大（现在是 ${skill.version ?? '没写'}）`)
    }
  }
}

if (errors.length > 0) {
  console.error(errors.map(e => `✗ ${e}`).join('\n'))
  process.exit(1)
}
console.log(`✓ ${index.skills.length} 个技能都没问题${base ? `（和 ${base} 比过版本号）` : ''}`)
