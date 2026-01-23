-- Automotive Repair Management System Database Schema
-- PostgreSQL Version
-- Compatible with Neon, Railway, Heroku PostgreSQL, and local PostgreSQL

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS public;

-- ============================================================================
-- Customer Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS customer (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(25),
    family_name VARCHAR(25) NOT NULL,
    email VARCHAR(320) NOT NULL,
    phone VARCHAR(11) NOT NULL
);

-- ============================================================================
-- Job Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS job (
    job_id SERIAL PRIMARY KEY,
    job_date DATE NOT NULL,
    customer INTEGER NOT NULL,
    total_cost DECIMAL(6,2) DEFAULT NULL,
    completed BOOLEAN DEFAULT FALSE,
    paid BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (customer) REFERENCES customer(customer_id)
        ON UPDATE CASCADE
);

-- ============================================================================
-- Part Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS part (
    part_id SERIAL PRIMARY KEY,
    part_name VARCHAR(25) NOT NULL,
    cost DECIMAL(5,2) NOT NULL
);

-- ============================================================================
-- Service Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS service (
    service_id SERIAL PRIMARY KEY,
    service_name VARCHAR(25) NOT NULL,
    cost DECIMAL(5,2) NOT NULL
);

-- ============================================================================
-- Job-Part Junction Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS job_part (
    job_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    qty INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (job_id, part_id),
    FOREIGN KEY (job_id) REFERENCES job(job_id)
        ON UPDATE CASCADE,
    FOREIGN KEY (part_id) REFERENCES part(part_id)
        ON UPDATE CASCADE
);

-- ============================================================================
-- Job-Service Junction Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS job_service (
    job_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    qty INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (job_id, service_id),
    FOREIGN KEY (job_id) REFERENCES job(job_id)
        ON UPDATE CASCADE,
    FOREIGN KEY (service_id) REFERENCES service(service_id)
        ON UPDATE CASCADE
);

-- ============================================================================
-- User Authentication Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS "user" (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(320) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'technician' CHECK (role IN ('technician', 'administrator')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    neon_auth_user_id VARCHAR(255) UNIQUE NULL
);

-- Create indexes for user table
CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_role ON "user"(role);

-- ============================================================================
-- Seed Data - Customers
-- ============================================================================
INSERT INTO customer (first_name, family_name, email, phone) VALUES
    ('Shannon', 'Willis', 'shannon@willis.nz', '0211661231'),
    ('Simon', 'Chambers', 'simonchambers@gmail.com', '033245678'),
    ('Charles', 'Carmichael', 'carmichaels@hotmail.com', '02754365286'),
    ('Zhe', 'Wang', 'zhe.wang@qq.com', '0743277893'),
    ('Qi', 'Qi', 'qi@qi.co.nz', '0294458423'),
    (NULL, 'Govindjee', 'hello@govindjee.nz', '034156784')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Seed Data - Parts
-- ============================================================================
INSERT INTO part (part_name, cost) VALUES
    ('Windscreen', 560.65),
    ('Headlight', 35.65),
    ('Wiper blade', 12.43),
    ('Left fender', 260.76),
    ('Right fender', 260.76),
    ('Tail light', 120.54),
    ('Hub Cap', 22.89)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Seed Data - Services
-- ============================================================================
INSERT INTO service (service_name, cost) VALUES
    ('Sandblast', 300.21),
    ('Minor Fill', 43.21),
    ('Major Fill', 125.70),
    ('Respray', 800.33),
    ('Touch up', 34.99),
    ('Polish', 250.00),
    ('Small Dent Removal', 49.99),
    ('Large Dent Removal', 249.00)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Seed Data - Jobs
-- ============================================================================
INSERT INTO job (job_date, customer, completed, paid, total_cost) VALUES
    ('2023-11-01', 4, TRUE, TRUE, 410.22),
    ('2024-02-02', 6, FALSE, FALSE, NULL),
    ('2023-12-11', 1, TRUE, FALSE, NULL),
    ('2023-12-12', 2, FALSE, FALSE, NULL),
    ('2023-12-12', 5, FALSE, FALSE, NULL)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Seed Data - Job Parts
-- ============================================================================
INSERT INTO job_part (job_id, part_id, qty) VALUES
    (1, 2, 2),
    (1, 4, 1)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Seed Data - Job Services
-- ============================================================================
INSERT INTO job_service (job_id, service_id, qty) VALUES
    (1, 2, 1),
    (1, 5, 1)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Default Administrator Account
-- ============================================================================
-- Note: Password should be changed on first login
-- Default password hash is a placeholder - generate a real one with:
-- python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_password'))"
INSERT INTO "user" (username, email, password_hash, role) VALUES
    ('admin', 'admin@autorepair.local', 'scrypt:32768:8:1$placeholder$changeme', 'administrator')
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- Trigger for updated_at column on user table
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_user_updated_at ON "user";
CREATE TRIGGER update_user_updated_at
    BEFORE UPDATE ON "user"
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
