const REPORT_FILENAME = /report_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.pdf/g
const REPORT_PATH_WITH_PREFIX = /[\w./\\-]*?(report_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.pdf)/g

export function cleanReportPaths(content: string): string {
  return content.replace(REPORT_PATH_WITH_PREFIX, '$1')
}

export function extractReportFilenames(content: string): string[] {
  const matches = content.match(REPORT_FILENAME) ?? []
  return [...new Set(matches)]
}
