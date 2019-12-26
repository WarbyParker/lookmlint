view: inventory_transfers {
  sql_table_name: public.inventory_transfers ;;

  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.id ;;
  }

  dimension: source_location_id {
    type: number
    sql: ${TABLE}.source_location_id ;;
  }

  dimension_group: created {
    type: time
    timeframes: [
      date,
      month,
      month_name,
      time,
      year
    ]
    sql: ${TABLE}.created ;;
  }

  dimension: destination_location_id {
    type: number
    sql: ${TABLE}.destination_location_id ;;
  }
}
