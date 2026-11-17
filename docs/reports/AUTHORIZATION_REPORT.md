# Mizigo Authorization Hardening Report

## Checks Added

1. `GET /users`
   - Added `require_admin_user` dependency.
   - Only authenticated users with role `ADMIN` may list users.
   - Non-admin authenticated users receive `403 Admin access required`.

2. `POST /payments`
   - Added an order ownership lookup before payment processing.
   - The order must exist before the payment service is called.
   - The authenticated user must own the target order.
   - Users attempting to pay for another user's order receive `403 Not authorized to process payment for this order`.

## Existing Checks Preserved

1. `POST /orders`
   - Orders are still created for `current_user.id` inside the existing order service.
   - No request body user ID is accepted, so users cannot create orders on behalf of another user through this endpoint.

2. `POST /products`
   - Product creation still requires the authenticated user to have role `VENDOR`.
   - Product creation still resolves the vendor account from `current_user.id`.
   - New products continue to be assigned only to the authenticated vendor's own vendor account.

3. `POST /vendors` and `POST /vendors/upgrade`
   - Vendor-only role checks remain in place.
   - Subscription upgrade still operates only on the vendor account linked to `current_user.id`.

## Notes

- Endpoint URLs were preserved.
- Database schema was not modified.
- Existing service-layer business logic was preserved.
- No new features were added.
- There are currently no order read/update endpoints and no product update/delete endpoints. The current authorization hardening covers the existing API surface.
