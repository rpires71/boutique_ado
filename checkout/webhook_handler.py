import json
import time

import stripe

from django.http import HttpResponse
from django.conf import settings

from products.models import Product
from .models import Order, OrderLineItem


class StripeWH_Handler:
    """Handle Stripe webhooks."""

    def __init__(self, request):
        """Store the request object."""
        self.request = request

    def handle_event(self, event):
        """Handle generic/unexpected webhook events."""
        return HttpResponse(
            content=f'Unhandled webhook received: {event["type"]}',
            status=200
        )

    def handle_payment_intent_succeeded(self, event):
        """
        Handle the payment_intent.succeeded webhook.
        """
        intent = event.data.object
        pid = intent.id

        bag = intent.metadata.bag if hasattr(intent.metadata, 'bag') else None
        save_info = intent.metadata.save_info if hasattr(intent.metadata, 'save_info') else None

        if not bag:
            return HttpResponse(
                content=(
                    f'Webhook received: {event["type"]} | '
                    'No bag metadata present, nothing to do.'
                ),
                status=200
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY
        charge = stripe.Charge.retrieve(intent.latest_charge)
        billing_details = charge.billing_details

        shipping_details = intent.shipping
        address = shipping_details.address if shipping_details else None

        grand_total = round(intent.amount_received / 100, 2)

        if address:
            if address.city == "":
                address.city = None
            if address.country == "":
                address.country = None
            if address.line1 == "":
                address.line1 = None
            if address.line2 == "":
                address.line2 = None
            if address.postal_code == "":
                address.postal_code = None
            if address.state == "":
                address.state = None

        order_exists = False
        attempt = 1
        order = None

        while attempt <= 5:
            try:
                order = Order.objects.get(
                    full_name__iexact=shipping_details.name if shipping_details else None,
                    email__iexact=billing_details.email,
                    phone_number__iexact=shipping_details.phone if shipping_details else None,
                    country__iexact=address.country if address else None,
                    postcode__iexact=address.postal_code if address else None,
                    town_or_city__iexact=address.city if address else None,
                    street_address1__iexact=address.line1 if address else None,
                    street_address2__iexact=address.line2 if address else None,
                    county__iexact=address.state if address else None,
                    grand_total=grand_total,
                    original_bag__iexact=bag,
                    stripe_pid=pid,
                )
                order_exists = True
                break

            except Order.DoesNotExist:
                attempt += 1
                time.sleep(1)

        if order_exists:
            return HttpResponse(
                content=(
                    f'Webhook received: {event["type"]} | '
                    f'Order already exists in database: {order.order_number}'
                ),
                status=200
            )

        try:
            order = Order.objects.create(
                full_name=shipping_details.name if shipping_details else None,
                email=billing_details.email,
                phone_number=shipping_details.phone if shipping_details else None,
                country=address.country if address else None,
                postcode=address.postal_code if address else None,
                town_or_city=address.city if address else None,
                street_address1=address.line1 if address else None,
                street_address2=address.line2 if address else None,
                county=address.state if address else None,
                original_bag=bag,
                stripe_pid=pid,
            )

            for item_id, item_data in json.loads(bag).items():
                product = Product.objects.get(id=item_id)

                if isinstance(item_data, int):
                    OrderLineItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item_data,
                    )
                else:
                    for size, quantity in item_data['items_by_size'].items():
                        OrderLineItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            product_size=size,
                        )

        except Exception as e:
            if order:
                order.delete()
            return HttpResponse(
                content=f'Webhook received: {event["type"]} | ERROR: {e}',
                status=500
            )

        return HttpResponse(
            content=(
                f'Webhook received: {event["type"]} | '
                f'Order was created in webhook: {order.order_number}'
            ),
            status=200
        )

    def handle_payment_intent_payment_failed(self, event):
        """Handle failed payments."""
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200
        )