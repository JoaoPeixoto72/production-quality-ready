#!/usr/bin/env node

// Copyright (c) 2026 João Carlos de Sousa Peixoto
// SPDX-License-Identifier: Apache-2.0

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url))
const SKILL_DIR = path.resolve(SCRIPT_DIR, '..')

const DELIMITER = '================================================================================'
const FILE_HEADER_PREFIX = 'FILE: '

const EXCLUDE_DIRS = new Set([
  '.git',
  'node_modules',
  '.audit',
  'results',
  'dist',
  'coverage'
])
const EXCLUDE_FILES = new Set([
  'seo-audit-all-in-one.txt',
  'seo-audit-bundle.txt',
  'seo-audit-bundle.md'
])

function argument(name, fallback = '') {
  const prefix = `--${name}=`
  const hit = process.argv.find((arg) => arg.startsWith(prefix))
  return hit ? hit.slice(prefix.length) : fallback
}

function hasFlag(name) {
  return process.argv.includes(`--${name}`)
}

function collectFiles(dir, baseDir = dir) {
  const results = []
  const entries = fs.readdirSync(dir, { withFileTypes: true })

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    const relPath = path.relative(baseDir, fullPath).replace(/\\/g, '/')

    if (entry.isDirectory()) {
      if (!EXCLUDE_DIRS.has(entry.name)) {
        results.push(...collectFiles(fullPath, baseDir))
      }
    } else if (entry.isFile()) {
      if (
        !EXCLUDE_FILES.has(entry.name) &&
        !entry.name.endsWith('-bundle.txt') &&
        !entry.name.endsWith('-bundle.md')
      ) {
        results.push({ fullPath, relPath })
      }
    }
  }

  return results
}

function getSkillVersion(skillDir) {
  try {
    const pkgPath = path.join(skillDir, 'package.json')
    if (fs.existsSync(pkgPath)) {
      const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'))
      if (pkg.version) return pkg.version
    }
  } catch {}

  try {
    const skillMd = fs.readFileSync(path.join(skillDir, 'SKILL.md'), 'utf8')
    const match = skillMd.match(/version:\s*([^\r\n]+)/)
    if (match) return match[1].trim()
  } catch {}

  return '1.0.0'
}

function pack(skillDir, outputFile) {
  const files = collectFiles(skillDir)

  // Sort: root files first, then by depth and alphabetically
  files.sort((a, b) => {
    const aDepth = a.relPath.split('/').length
    const bDepth = b.relPath.split('/').length
    if (aDepth !== bDepth) return aDepth - bDepth
    return a.relPath.localeCompare(b.relPath)
  })

  let totalBytes = 0
  let totalLines = 0
  const fileEntries = []

  for (const file of files) {
    const content = fs.readFileSync(file.fullPath, 'utf8')
    const bytes = Buffer.byteLength(content, 'utf8')
    const lines = content.split('\n').length
    totalBytes += bytes
    totalLines += lines
    fileEntries.push({
      relPath: file.relPath,
      content,
      bytes,
      lines
    })
  }

  const version = getSkillVersion(skillDir)

  const lines = [
    DELIMITER,
    `SKILL BUNDLE: seo-audit (v${version})`,
    `Generated at: ${new Date().toISOString()}`,
    `Total files:  ${fileEntries.length}`,
    `Total lines:  ${totalLines}`,
    `Total size:   ${(totalBytes / 1024).toFixed(2)} KB (${totalBytes} bytes)`,
    DELIMITER,
    '',
    '## INSTRUCTIONS FOR AI ASSISTANTS / CONSUMERS:',
    'This single file contains the complete file tree and exact source code of the',
    'seo-audit skill. Each file begins with a header banner in the following format:',
    '',
    '--------------------------------------------------------------------------------',
    `${FILE_HEADER_PREFIX}<relative_path>`,
    '--------------------------------------------------------------------------------',
    '<raw content of file>',
    '',
    'To extract all files automatically into their original folder structure using Node.js:',
    '  node scripts/bundle_skill.mjs --unpack=seo-audit-all-in-one.txt --dest=output_folder',
    'or using a one-liner:',
    '  node -e \'const fs=require("fs"),p=require("path"),raw=fs.readFileSync("seo-audit-all-in-one.txt","utf8"),idx=raw.indexOf("FILE CONTENTS BEGIN"),c=idx!==-1?raw.slice(idx):raw,re=/={80}\\r?\\nFILE: (.*?)\\r?\\n={80}\\r?\\n([\\s\\S]*?)(?=\\r?\\n={80}\\r?\\nFILE: |$)/g;let m;while(m=re.exec(c)){const f=m[1].trim(),t=p.resolve(f);fs.mkdirSync(p.dirname(t),{recursive:true});fs.writeFileSync(t,m[2])};console.log("Unpacked successfully!")\'',
    '',
    DELIMITER,
    'TABLE OF CONTENTS (FILE TREE):',
    DELIMITER
  ]

  for (const file of fileEntries) {
    const sizeKb = (file.bytes / 1024).toFixed(2)
    lines.push(
      `  - ${file.relPath.padEnd(52)} (${String(file.lines).padStart(5)} lines, ${sizeKb.padStart(7)} KB)`
    )
  }

  lines.push('', DELIMITER, 'FILE CONTENTS BEGIN', DELIMITER, '')

  for (const file of fileEntries) {
    lines.push(DELIMITER)
    lines.push(`${FILE_HEADER_PREFIX}${file.relPath}`)
    lines.push(DELIMITER)
    lines.push(file.content)
    if (!file.content.endsWith('\n')) lines.push('')
  }

  const bundledText = lines.join('\n')
  fs.writeFileSync(outputFile, bundledText, 'utf8')
  return { fileEntries, totalBytes, totalLines, outputFile }
}

function unpack(bundlePath, targetDir) {
  const fullContent = fs.readFileSync(bundlePath, 'utf8')
  const marker = 'FILE CONTENTS BEGIN'
  const startIndex = fullContent.indexOf(marker)
  const content =
    startIndex !== -1 ? fullContent.slice(startIndex + marker.length) : fullContent

  const regex =
    /={80}\r?\nFILE: (.*?)\r?\n={80}\r?\n([\s\S]*?)(?=\r?\n={80}\r?\nFILE: |$)/g

  let count = 0
  let match

  while ((match = regex.exec(content)) !== null) {
    const relPath = match[1].trim()
    const fileContent = match[2]
    const dest = path.resolve(targetDir, relPath)
    fs.mkdirSync(path.dirname(dest), { recursive: true })
    fs.writeFileSync(dest, fileContent, 'utf8')
    console.log(`Extracted: ${relPath}`)
    count++
  }

  console.log(`\nSuccessfully unpacked ${count} files to ${targetDir}`)
}

function main() {
  if (hasFlag('help')) {
    console.log(`Usage:
  node scripts/bundle_skill.mjs [options]

Options:
  --out=<path>       Output bundle text file (default: seo-audit-all-in-one.txt)
  --unpack=<bundle>  Extract all files from a bundle file
  --dest=<path>      Destination directory for unpacking (default: .)
  --help             Show help`)
    return
  }

  const unpackFile = argument('unpack')
  if (unpackFile) {
    const targetDir = path.resolve(argument('dest', process.cwd()))
    unpack(path.resolve(unpackFile), targetDir)
    return
  }

  const defaultOut = path.join(SKILL_DIR, 'seo-audit-all-in-one.txt')
  const outFile = path.resolve(argument('out', defaultOut))

  const { fileEntries, totalBytes, totalLines, outputFile } = pack(
    SKILL_DIR,
    outFile
  )

  console.log(`\nSkill bundled successfully into: ${outputFile}`)
  console.log(`Total files: ${fileEntries.length}`)
  console.log(`Total lines: ${totalLines}`)
  console.log(
    `Total size:  ${(totalBytes / 1024).toFixed(2)} KB (${totalBytes} bytes)\n`
  )
}

main()
