def build_thermal_text(payload: dict) -> str:
    store = payload.get('store', {})
    customer = payload.get('customer', {})
    items = payload.get('items', [])
    totals = payload.get('totals', {})

    lines = []
    lines.append('       OORVASHEE SAREE HOUSE')
    lines.append('        Thank you for shopping')
    lines.append('-' * 42)

    # Bill Number
    bill_no = (
        payload.get('bill_no')
        or payload.get('order_number')
        or payload.get('invoice_no')
        or payload.get('order_id')
        or ''
    )
    lines.append(f"Bill No: {bill_no}")

    # Date
    lines.append(f"Date   : {payload.get('date') or ''}")

    if store.get('name'):
        lines.append(f"Store  : {store.get('name')}")

    lines.append('-' * 42)

    if customer.get('name'):
        lines.append(f"Customer: {customer.get('name')}")

    if customer.get('phone'):
        lines.append(f"Phone   : {customer.get('phone')}")

    lines.append('-' * 42)
    lines.append('ITEM                 QTY   RATE   AMOUNT')
    lines.append('-' * 42)

    calculated_total = 0

    for item in items:
        name = str(item.get('name', 'Item'))[:18]
        qty = float(item.get('qty', 1))
        rate = float(item.get('price', 0))
        amount = float(item.get('amount', qty * rate))

        calculated_total += amount

        lines.append(
            f"{name:<18} {int(qty):>3} {rate:>6.0f} {amount:>8.0f}"
        )

    lines.append('-' * 42)

    if totals.get('subtotal') is not None:
        lines.append(
            f"Subtotal:{float(totals.get('subtotal',0)):>32.2f}"
        )

    if totals.get('discount'):
        lines.append(
            f"Discount:{float(totals.get('discount',0)):>32.2f}"
        )

    if totals.get('gst'):
        lines.append(
            f"GST     :{float(totals.get('gst',0)):>32.2f}"
        )

    # Final Total
    final_total = payload.get('total')

    if final_total is None:
        final_total = totals.get('total')

    if final_total is None:
        final_total = calculated_total

    lines.append(f"TOTAL   :{float(final_total):>32.2f}")

    lines.append('-' * 42)

    lines.append(
        f"Payment : {payload.get('payment_status', payload.get('payment', 'PAID'))}"
    )

    lines.append('No exchange without bill.')
    lines.append('Visit Again - Oorvashee.com')
    lines.append('\n\n')

    return '\n'.join(lines)
