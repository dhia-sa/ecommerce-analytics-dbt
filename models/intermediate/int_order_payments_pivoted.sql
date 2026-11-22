-- One row per order: total paid and the amount paid with each payment method
with payments as (
    select * from {{ ref('stg_olist__order_payments') }}
)

select
    order_id,
    count(*)                                                        as payment_count,
    max(payment_installments)                                       as max_installments,
    sum(payment_value)                                              as total_payment,
    sum(payment_value) filter (where payment_type = 'credit_card')  as credit_card_amount,
    sum(payment_value) filter (where payment_type = 'boleto')       as boleto_amount,
    sum(payment_value) filter (where payment_type = 'voucher')      as voucher_amount,
    sum(payment_value) filter (where payment_type = 'debit_card')   as debit_card_amount,
    -- payment method that covered the largest share of the order
    arg_max(payment_type, payment_value)                            as main_payment_type
from payments
group by order_id
