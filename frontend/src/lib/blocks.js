// ui_block payload shapes - single source of truth is backend/app/tools.py.
// Kept as JSDoc typedefs (CRA template is plain JS; see DEVIATIONS.md).
/**
 * @typedef {Object} Product  // _card() in tools.py
 * @property {string} ps_number  @property {string} mpn  @property {string} brand
 * @property {string} title  @property {number|null} price  @property {string} availability
 * @property {string|null} install_difficulty  @property {string|null} install_time
 * @property {number|null} rating  @property {number|null} review_count
 * @property {string|null} image_url  @property {string} product_url
 *
 * Block types: product_list {products[]} · product_card {product, description,
 * symptoms[]} · compat_result {verdict, part, model, evidence_count,
 * honesty_note} · diagnosis {causes[{rank, cause}], suggested_parts[]} ·
 * install_guide {part, difficulty, time, video_url, stories[]} ·
 * order_status {order_id, status, eta, carrier}
 */
export {};
