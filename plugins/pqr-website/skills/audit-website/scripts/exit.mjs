/**
 * Exit an engine without libuv's Windows race: `process.exit()` while async handles
 * close aborts with `UV_HANDLE_CLOSING` (0xC0000409) after printing the report.
 * Set `exitCode`, let it drain, and an unref'd timer closes it if something lingers.
 */
export function exitCleanly(code, { graceMs = 250 } = {}) {
  process.exitCode = code
  const timer = setTimeout(() => process.exit(code), graceMs)
  if (typeof timer.unref === 'function') timer.unref()
}
