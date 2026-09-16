# Webhook Delivery Service

## Purpose

Partner systems submit signed event payloads. The service accepts valid events
and delivers each event to the callback URL registered for its subscription.

## User Story

As a subscription owner, I want accepted partner events delivered to my callback
even when a temporary connection failure prevents the first attempt.

## Requirements

- `POST /deliveries` accepts a JSON event containing an event ID, subscription
  ID, event type, and payload. A successful request returns a delivery ID and
  HTTP 202. Malformed requests return HTTP 400 with a machine-readable error.
- Each request includes a timestamp and an HMAC-SHA256 signature of the timestamp
  and exact request-body bytes. The service verifies the signature using the
  subscription's configured secret before accepting the event. Invalid
  signatures or timestamps older than five minutes return HTTP 401.
- An accepted event is sent as an HTTP POST to the subscription's callback.
  A 2xx response completes the delivery. Connection timeouts and 5xx responses
  schedule another attempt, up to five total attempts. Other 4xx responses end
  the delivery without another attempt.
- Attempts after the first wait 1, 5, 30, and 120 minutes respectively.
  Repeated submissions of the same event ID for the same subscription return
  the existing delivery ID rather than creating another delivery.
- `GET /deliveries/{delivery_id}` returns the delivery state, attempt count,
  and last response status without exposing the subscription secret.

## Scope

One registered callback per subscription. Subscription creation, secret
rotation, and a browser interface are outside this feature.
