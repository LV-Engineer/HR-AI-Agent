CREATE SCHEMA IF NOT EXISTS auth;

CREATE EXTENSION IF NOT EXISTS pgcrypto SCHEMA auth;

CREATE TABLE auth.users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE auth.refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    family_id   UUID NOT NULL,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE FUNCTION auth.create_user(p_email TEXT, p_password TEXT)
RETURNS UUID
LANGUAGE plpgsql
AS $function$
DECLARE
    new_id UUID;
BEGIN
    INSERT INTO auth.users (email, password_hash)
    VALUES (p_email, auth.crypt(p_password, auth.gen_salt('bf', 12)))
    RETURNING id INTO new_id;

    RETURN new_id;
END;
$function$;