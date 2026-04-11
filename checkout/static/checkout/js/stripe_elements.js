const stripePublicKey = JSON.parse(
    document.getElementById('id_stripe_public_key').textContent
);
const clientSecret = JSON.parse(
    document.getElementById('id_client_secret').textContent
);

const stripe = Stripe(stripePublicKey);
const elements = stripe.elements();

const style = {
    base: {
        color: '#000',
        fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
        fontSmoothing: 'antialiased',
        fontSize: '16px',
        '::placeholder': {
            color: '#aab7c4',
        },
    },
    invalid: {
        color: '#dc3545',
        iconColor: '#dc3545',
    },
};

const card = elements.create('card', { style: style });
card.mount('#card-element');

card.on('change', function (event) {
    const errorDiv = document.getElementById('card-errors');
    if (event.error) {
        errorDiv.innerHTML = `
            <span class="icon" role="alert">
                <i class="fas fa-times"></i>
            </span>
            <span>${event.error.message}</span>
        `;
    } else {
        errorDiv.textContent = '';
    }
});

const form = document.getElementById('payment-form');
const cardErrors = document.getElementById('card-errors');
const submitButton = document.getElementById('submit-button');
const loadingOverlay = document.getElementById('loading-overlay');

form.addEventListener('submit', async function (ev) {
    ev.preventDefault();

    card.update({ disabled: true });
    submitButton.disabled = true;
    loadingOverlay.style.display = 'block';

    const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
            card: card,
            billing_details: {
                name: document.getElementById('id_full_name')?.value.trim() || '',
                email: document.getElementById('id_email')?.value.trim() || '',
                phone: document.getElementById('id_phone_number')?.value.trim() || '',
                address: {
                    line1: document.getElementById('id_street_address1')?.value.trim() || '',
                    line2: document.getElementById('id_street_address2')?.value.trim() || '',
                    city: document.getElementById('id_town_or_city')?.value.trim() || '',
                    state: document.getElementById('id_county')?.value.trim() || '',
                    postal_code: document.getElementById('id_postcode')?.value.trim() || '',
                    country: document.getElementById('id_country')?.value || '',
                },
            },
        },
    });

    if (result.error) {
        cardErrors.innerHTML = `
            <span class="icon" role="alert">
                <i class="fas fa-times"></i>
            </span>
            <span>${result.error.message}</span>
        `;
        loadingOverlay.style.display = 'none';
        card.update({ disabled: false });
        submitButton.disabled = false;
    } else {
        if (result.paymentIntent && result.paymentIntent.status === 'succeeded') {
            form.submit();
        } else {
            cardErrors.textContent = 'Payment processing issue. Please try again.';
            loadingOverlay.style.display = 'none';
            card.update({ disabled: false });
            submitButton.disabled = false;
        }
    }
});