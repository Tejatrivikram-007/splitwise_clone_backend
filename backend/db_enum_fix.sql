-- Add missing values to splittypeenum enum type in PostgreSQL
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'splittypeenum') THEN
        CREATE TYPE splittypeenum AS ENUM ('EQUAL', 'PERCENTAGE', 'EXACT');
    ELSE
        BEGIN
            ALTER TYPE splittypeenum ADD VALUE IF NOT EXISTS 'EQUAL';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END;
        BEGIN
            ALTER TYPE splittypeenum ADD VALUE IF NOT EXISTS 'PERCENTAGE';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END;
        BEGIN
            ALTER TYPE splittypeenum ADD VALUE IF NOT EXISTS 'EXACT';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END;
    END IF;
END$$;
