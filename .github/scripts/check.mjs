#!/usr/bin/env node
/**
 * 技能库的检查：index.json 和每个 SKILL.md 对得上，每个技能有版本号和作者，
 * 放在 games/<游戏>/<脚本或 _game>/<作者>/<技能名>/ 或 general/<作者>/<技能名>/，
 * 不是官方的技能名以「作者-」开头，脚本包（adg.script.yaml）和游戏包
 * （game.yaml）的 id 和名字对得上，history 从新到旧、每一版都有标签；
 * 给了一个 git 提交（上一个版本）时，再查改过文件的技能升了版本号，
 * 旧版本写进了 history（只是挪了文件夹的不算改过）。
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
const AUTHOR = /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$/
const OFFICIAL = 'MultiGameAssistant'
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

const git = (...args) => execFileSync('git', args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
/** The tags there are (<技能名>@<版本>); undefined: no git here. */
let tags
try { tags = new Set(git('tag', '-l').split('\n').filter(Boolean)) } catch { tags = undefined }

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
  if (skill.default !== undefined && typeof skill.default !== 'boolean') fail(`${where}：default 只能是 true 或 false`)
  // 作者：上传的人的 GitHub 用户名。不是官方的，技能名以「作者名-」开头，全库不会重名。
  if (!AUTHOR.test(skill.author ?? '')) fail(`${where}：author 写上传的人的 GitHub 用户名`)
  else if (skill.author !== OFFICIAL && !skill.name?.startsWith(`${skill.author.toLowerCase()}-`)) fail(`${where}：不是官方的技能，名字要以「${skill.author.toLowerCase()}-」开头`)
  // 目录：游戏 → 脚本（游戏本身的用 _game）→ 作者 → 技能名；通用的：general → 作者 → 技能名。
  const parts = skill.path.split('/')
  const ownGame = existsSync(join(skill.path, 'game.yaml')) || (skill.scripts ?? []).length === 0
  if (parts[0] === 'games') {
    const [, game, script, author, folder] = parts
    if (parts.length !== 5) fail(`${where}：path 要是 games/<游戏 id>/<脚本 id 或 _game>/<作者>/<技能名>`)
    else {
      if (!(skill.games ?? []).includes(game)) fail(`${where}：games 要包括它所在的游戏 ${game}`)
      if (ownGame ? script !== '_game' : !(skill.scripts ?? []).includes(script)) fail(`${where}：第三层文件夹${ownGame ? '用 _game（游戏本身的）' : `用它的脚本 id（${(skill.scripts ?? []).join(' / ')}）`}，现在是 ${script}`)
      if (author !== skill.author) fail(`${where}：作者文件夹（${author}）要和 author（${skill.author ?? '没写'}）一样`)
      if (folder !== skill.name) fail(`${where}：最后一层文件夹名要用技能名 ${skill.name}`)
    }
  } else if (parts[0] === 'general') {
    if (parts.length !== 3 || parts[1] !== skill.author || parts[2] !== skill.name) fail(`${where}：通用技能的 path 要是 general/<作者>/<技能名>`)
  } else fail(`${where}：path 要放在 games/ 或 general/ 下`)
  // history：以前发布过、用户还能换回去的版本，从新到旧，都比 version 旧，每一版都有标签 <技能名>@<版本>。
  if (skill.history !== undefined) {
    if (!Array.isArray(skill.history)) fail(`${where}：history 要是列表`)
    else {
      let newer = skill.version
      for (const old of skill.history) {
        if (!VERSION.test(old?.version ?? '')) { fail(`${where}：history 里的 version 要写成 主.次.修订`); continue }
        if (VERSION.test(newer ?? '') && compare(old.version, newer) >= 0) fail(`${where}：history 要从新到旧，而且都比当前版本旧（${old.version}）`)
        newer = old.version
        if (old.changes !== undefined && (typeof old.changes !== 'string' || old.changes.length > 300)) fail(`${where}：history 里 ${old.version} 的 changes 写一句就够`)
        if (tags !== undefined && !tags.has(`${skill.name}@${old.version}`)) fail(`${where}：history 里的 ${old.version} 没有标签 ${skill.name}@${old.version}（只写发布过的版本）`)
      }
    }
  }
  // 脚本包：软件按文件夹名（技能名）找它，id 要一样。
  const pack = join(skill.path, 'adg.script.yaml')
  if (existsSync(pack)) {
    const id = /^id:\s*([\w-]+)\s*$/m.exec(readFileSync(pack, 'utf8'))?.[1]
    if (id !== skill.name) fail(`${pack}：id（${id ?? '没写'}）要和技能名「${skill.name}」一样`)
    if (skill.kind !== 'script') fail(`${where}：带脚本包的技能 kind 要写 script`)
  }
  // 游戏包：技能名是 game-<游戏 id>。
  const game = join(skill.path, 'game.yaml')
  if (existsSync(game)) {
    const id = /^id:\s*([\w-]+)\s*$/m.exec(readFileSync(game, 'utf8'))?.[1]
    if (id === undefined || skill.name !== `game-${id}`) fail(`${game}：id（${id ?? '没写'}）对应的技能名要是 game-<id>（现在是「${skill.name}」）`)
    if (skill.kind !== 'game') fail(`${where}：带游戏包的技能 kind 要写 game`)
    if (id !== undefined && skill.games !== undefined && !skill.games.includes(id)) fail(`${where}：games 要包括它自己的游戏 ${id}`)
  }
  if (existsSync(pack) && existsSync(game)) fail(`${where}：一个文件夹只能是脚本包或游戏包之一`)
}

// 和上一个版本比：改了文件夹里任何文件的技能，版本号要比原来大。
const base = process.argv[2]
if (base !== undefined && base !== '' && !/^0+$/.test(base)) {
  let before
  try {
    before = JSON.parse(git('show', `${base}:index.json`).replace(/^﻿/, ''))
  } catch {
    before = { skills: [] }
  }
  // 只是挪了地方（文件没变）的不算改过。
  const changed = git('diff', '--name-status', '-M', base).split('\n').filter(Boolean).flatMap(line => {
    const [status, ...files] = line.split('\t')
    return status === 'R100' ? [] : files
  })
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
  // 升了版本号：发布过的旧版本（有标签的）写进 history，用户才换得回去。
  for (const skill of index.skills ?? []) {
    const old = before.skills?.find(s => s.name === skill.name)
    if (old === undefined || !VERSION.test(old.version ?? '') || old.version === skill.version) continue
    if (tags?.has(`${skill.name}@${old.version}`) === true && !(skill.history ?? []).some(h => h.version === old.version)) {
      fail(`「${skill.name}」升了版本号：把旧的 ${old.version}（和它的 changes）写进 history 的最前面，用户才能换回去`)
    }
  }
}

if (errors.length > 0) {
  console.error(errors.map(e => `✗ ${e}`).join('\n'))
  process.exit(1)
}
console.log(`✓ ${index.skills.length} 个技能都没问题${base ? `（和 ${base} 比过版本号）` : ''}`)
