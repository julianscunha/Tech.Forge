/** `/modules/:id` (e qualquer sub-rota) — usado por AppShell, ModuleWorkspace
 * e Breadcrumb pra concordarem sobre quando uma aba de módulo está visível. */
export function isModuleRoute(pathname: string): boolean {
  return /^\/modules\/[^/]+/.test(pathname)
}
