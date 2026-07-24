/** PRD 부록 A 장르(shcate) 코드 */
export const SHCATE_OPTIONS = [
  { code: 'AAAA', label: '연극' },
  { code: 'GGGA', label: '뮤지컬' },
  { code: 'CCCA', label: '서양음악' },
  { code: 'CCCC', label: '한국음악' },
  { code: 'BBBC', label: '무용' },
  { code: 'EEEB', label: '서커스·마술' },
  { code: 'EEEA', label: '복합' },
]

const SHCATE_CODES = new Set(SHCATE_OPTIONS.map((item) => item.code))

export function isValidShcate(value) {
  return SHCATE_CODES.has(value)
}
