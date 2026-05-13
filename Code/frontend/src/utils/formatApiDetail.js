/**
 * FastAPI often returns `detail` as a string, a single object, or an array of
 * `{ loc, msg, type, ... }` validation errors. React cannot render those as children.
 *
 * @param {unknown} detail - `error.response?.data?.detail` from Axios
 * @returns {string}
 */
export function formatApiDetail(detail) {
  if (detail == null || detail === '') return '';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object' && typeof item.msg === 'string') return item.msg;
        return '';
      })
      .filter(Boolean)
      .join(' ');
  }
  if (typeof detail === 'object') {
    if (typeof detail.msg === 'string') return detail.msg;
    try {
      return JSON.stringify(detail);
    } catch {
      return 'Request failed';
    }
  }
  return String(detail);
}
