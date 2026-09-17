# Webhook Delivery Service Plan

## Components

- A TypeScript HTTP service receives requests, retains the raw request body,
  verifies its timestamp and signature, and validates the event fields.
- A delivery store records subscription ID, event ID, delivery ID, state,
  attempt count, next attempt time, and last response status. The pair of
  subscription ID and event ID is unique.
- A worker selects due deliveries, sends the event to its registered callback,
  and records each attempt before calculating the next attempt time.

## Request Flow

1. Resolve the subscription and verify the signed raw request bytes.
2. Validate the JSON event and find or create its delivery record.
3. Return the delivery ID while the worker processes the accepted event.
4. For an outbound attempt, record the result and either finish the delivery or
   schedule its next attempt according to the intervals in spec.md.

## Local Development Inputs

Use an in-process clock and a callback stub that can return a response status
or a connection timeout. No real callback URL or signing secret is included in
these project documents.
