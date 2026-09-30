/**
 * Sai de um motor sem a corrida do libuv no Windows.
 *
 * O defeito que isto resolve (2026-09-30): os dois motores de website
 * imprimiam o relatório inteiro e abortavam a seguir com
 *
 *     Assertion failed: !(handle->flags & UV_HANDLE_CLOSING),
 *     file src\win\async.c, line 94        (exit 0xC0000409)
 *
 * Um instrumento que faz o trabalho e morre a seguir parece avariado — e um
 * alvo `http://` local, que é o alvo natural de qualquer verificação antes de
 * um deploy, era exactamente o caso que o disparava.
 *
 * `process.exit()` corre com o encerramento dos handles assíncronos (stdout
 * num pipe, sockets keep-alive do `fetch`). Aqui o código de saída vai para
 * `process.exitCode` — o runner lê-o da mesma maneira — e o processo é deixado
 * drenar. Se algo o mantiver vivo, um temporizador *unref'd* fecha-o depois de
 * uma janela de tolerância, quando os handles já assentaram.
 */
export function exitCleanly(code, { graceMs = 250 } = {}) {
  process.exitCode = code
  const timer = setTimeout(() => process.exit(code), graceMs)
  if (typeof timer.unref === 'function') timer.unref()
}
