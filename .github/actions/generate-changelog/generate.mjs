#!/usr/bin/env node
import { execSync } from 'node:child_process';
import { appendFileSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const version = process.env.RELEASE_VERSION;
const cwd = process.env.WORKING_DIRECTORY || '.';

if (!version) {
  console.error('::error::RELEASE_VERSION env var is required');
  process.exit(1);
}

let prevTag = '';
try {
  prevTag = execSync('git describe --tags --abbrev=0 HEAD^', {
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'ignore'],
  }).trim();
} catch {
  // No prior tag — first release. Range falls back to full history.
}

const range = prevTag ? `${prevTag}..HEAD` : 'HEAD';
const subjects = execSync(`git log ${range} --pretty=format:%s --no-merges`, {
  encoding: 'utf8',
})
  .split('\n')
  .filter(Boolean);

const typeToSection = {
  feat: 'Features',
  fix: 'Fixes',
  docs: 'Documentation',
  perf: 'Performance',
  refactor: 'Refactoring',
  test: 'Tests',
  build: 'Build',
  ci: 'CI',
  style: 'Style',
  chore: 'Chores',
};

const sectionOrder = [
  'Features',
  'Fixes',
  'Documentation',
  'Performance',
  'Refactoring',
  'Tests',
  'Build',
  'CI',
  'Style',
  'Chores',
];

const groups = Object.fromEntries(sectionOrder.map((s) => [s, []]));
const breaking = [];
const other = [];

const commitRe = /^(\w+)(?:\(([^)]+)\))?(!)?:\s+(.+)$/;

for (const subject of subjects) {
  const m = subject.match(commitRe);
  if (!m) {
    other.push(`- ${subject}`);
    continue;
  }
  const [, type, , bang] = m;
  const entry = `- ${subject}`;
  if (bang === '!') breaking.push(entry);
  const section = typeToSection[type];
  if (section) {
    groups[section].push(entry);
  } else {
    other.push(entry);
  }
}

const now = new Date();
const dd = String(now.getDate()).padStart(2, '0');
const mm = String(now.getMonth() + 1).padStart(2, '0');
const yyyy = now.getFullYear();
const date = `${dd}/${mm}/${yyyy}`;

const lines = [`## v${version} - ${date}`];

if (breaking.length) {
  lines.push('', '### Breaking changes', ...breaking);
}
for (const name of sectionOrder) {
  if (groups[name].length) {
    lines.push('', `### ${name}`, ...groups[name]);
  }
}
if (other.length) {
  lines.push('', '### Other', ...other);
}

const entry = `${lines.join('\n')}\n`;

const clPath = join(cwd, 'CHANGELOG.md');
let existing = '';
if (existsSync(clPath)) {
  existing = readFileSync(clPath, 'utf8');
}

let next;
if (existing.startsWith('# Changelog')) {
  const firstNewline = existing.indexOf('\n');
  const title = existing.slice(0, firstNewline + 1);
  const rest = existing.slice(firstNewline + 1).replace(/^\n+/, '');
  next = `${title}\n${entry}\n${rest}`;
} else {
  next = `# Changelog\n\n${entry}\n${existing}`;
}

writeFileSync(clPath, next);
console.log(`CHANGELOG.md updated with v${version} (${subjects.length} commits).`);

const outFile = process.env.GITHUB_OUTPUT;
if (outFile) {
  appendFileSync(outFile, `body<<__EOF__\n${entry}__EOF__\n`);
}
