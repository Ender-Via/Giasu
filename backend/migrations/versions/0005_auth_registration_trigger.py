"""Tạo index email chữ thường và trigger đồng bộ tài khoản khi đăng ký Supabase Auth.

Revision ID: 0005_auth_registration_trigger
Revises: 0004_tutor_profiles
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_auth_registration_trigger"
down_revision: str | None = "0004_tutor_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_users_login_identifier_lower",
        "users",
        [sa.text("lower(login_identifier)")],
        unique=True,
    )
    op.execute(
        """
        CREATE FUNCTION public.handle_giasu_registration()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = ''
        AS $$
        DECLARE
            business_user_id uuid := gen_random_uuid();
            registration_role text := NEW.raw_user_meta_data ->> 'role';
            registration_name text := btrim(NEW.raw_user_meta_data ->> 'full_name');
            registration_phone text := NEW.raw_user_meta_data ->> 'phone';
            role_id smallint;
        BEGIN
            IF NEW.raw_user_meta_data IS NULL
               OR (
                   NEW.raw_user_meta_data ->> 'registration_source'
               ) IS DISTINCT FROM 'giasu-register'
            THEN
                RETURN NEW;
            END IF;

            IF registration_role NOT IN ('Tutor', 'Parent')
               OR registration_name IS NULL
               OR char_length(registration_name) NOT BETWEEN 2 AND 100
               OR registration_phone IS NULL
               OR registration_phone !~ '^0[0-9]{9}$'
               OR COALESCE((NEW.raw_user_meta_data ->> 'accept_terms')::boolean, false) IS NOT TRUE
            THEN
                RAISE EXCEPTION 'Dữ liệu đăng ký không hợp lệ' USING ERRCODE = 'check_violation';
            END IF;

            role_id := CASE registration_role WHEN 'Tutor' THEN 2 ELSE 3 END;
            INSERT INTO public.users (
                id, auth_user_id, role_id, full_name, login_identifier,
                credential_reference, is_active, token_version, created_at
            )
            VALUES (
                business_user_id, NEW.id, role_id, registration_name, lower(NEW.email),
                NULL, true, 0, now()
            );

            IF registration_role = 'Tutor' THEN
                INSERT INTO public.tutors (
                    user_id, phone, verification_status, reputation_score
                ) VALUES (business_user_id, registration_phone, 'Unverified', 0);
            ELSE
                INSERT INTO public.parents (user_id, phone, reputation_score)
                VALUES (business_user_id, registration_phone, 0);
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION public.handle_giasu_registration() FROM PUBLIC")
    op.execute(
        """
        CREATE TRIGGER on_giasu_auth_user_created
        AFTER INSERT ON auth.users
        FOR EACH ROW EXECUTE FUNCTION public.handle_giasu_registration()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS on_giasu_auth_user_created ON auth.users")
    op.execute("DROP FUNCTION IF EXISTS public.handle_giasu_registration()")
    op.drop_index("ix_users_login_identifier_lower", table_name="users")
