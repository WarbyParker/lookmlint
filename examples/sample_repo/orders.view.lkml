view: orders {
  sql_table_name: public.orders ;;

  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.id ;;
  }

  dimension: placed {
    type: time
    sql: ${TABLE}.placed ;;
  }

  measure: count {
    type: count
  }
}
