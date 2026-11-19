#!/usr/bin/env node
/**
 * 给每个技能的当前版本打一个 git 标签 `<技能名>@<版本>`（已经有的不动），
 * 打在现在的提交上。软件按这个标签下载那一版，用户往前往后都能换。
 * 推送到 main 后由 .github/workflows/check.yml 运行，之后 `git push origin --tags`。
 *
 *   node .github/scripts/tag.mjs
 */
import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'

const git = (...args) => execFileSync('git', args, { encoding: 'utf8' })
const has = tag => { try { git('rev-parse', '-q', '--verify', `refs/tags/${tag}`); return true } catch { return false } }
const index = JSON.parse(readFileSync('index.json', 'utf8').replace(/^﻿/, ''))
let made = 0
for (const skill of index.skills ?? []) {
  if (typeof skill.version !== 'string') continue
  const tag = `${skill.name}@${skill.version}`
  if (has(tag)) continue
  git('tag', tag)
  console.log(`+ ${tag}`)
  made += 1
}
console.log(made === 0 ? '没有新版本要打标签' : `打了 ${made} 个标签`)
