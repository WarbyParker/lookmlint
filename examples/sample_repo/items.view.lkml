# issues with this view:
# - lacks a primary_key dimension
# - lacks a sql reference, despite having ${TABLE} references in dimension sql
# - view name does not match view file name

view: order_items {

  dimension: order_id {
    type: number
    sql: ${TABLE}.order_id ;;
  }

  dimension: product_id {
    type: number
    sql: ${TABLE}.product_id ;;
  }

  dimension: qty {
    type: number
    sql: ${TABLE}.qty ;;
  }

  dimension: unit_cost_usd {
    type: number
    sql: ${TABLE}.unit_cost_usd ;;
  }

  dimension_group: created {
    type: time
    timeframes: [
      date,
      month,
      year
    ]
    sql: ${TABLE}.created ;;
  }

  measure: count {
    type: count
  }
}
