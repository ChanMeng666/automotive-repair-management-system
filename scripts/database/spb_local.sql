-- Automotive Repair Management System Database Schema
-- Version: 2.0

create schema if not exists spb;

use spb;

CREATE TABLE IF NOT EXISTS customer
(
customer_id INT auto_increment PRIMARY KEY NOT NULL,
first_name varchar(25),
family_name varchar(25) not null,
email varchar(320) not null,
phone varchar(11) not null
);


 CREATE TABLE IF NOT EXISTS job
(
job_id INT auto_increment PRIMARY KEY NOT NULL,
job_date date NOT NULL,
customer int NOT NULL,
total_cost decimal(6,2) default null,
completed tinyint default 0,
paid tinyint default 0,

FOREIGN KEY (customer) REFERENCES customer(customer_id)
ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS part
(
part_id INT auto_increment PRIMARY KEY NOT NULL,
part_name varchar(25) not null ,
cost decimal(5,2) not null
);

CREATE TABLE IF NOT EXISTS service
(
service_id INT auto_increment PRIMARY KEY NOT NULL,
service_name varchar(25) not null ,
cost decimal(5,2) not null
);

CREATE TABLE IF NOT EXISTS job_part
(
job_id INT NOT NULL,
part_id  INT not null ,
qty INT not null DEFAULT 1,
FOREIGN KEY (job_id) REFERENCES job(job_id)
ON UPDATE CASCADE,
FOREIGN KEY (part_id) REFERENCES part(part_id)
ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS job_service
(
job_id INT NOT NULL,
service_id  INT not null ,
qty INT not null DEFAULT 1,
FOREIGN KEY (job_id) REFERENCES job(job_id)
ON UPDATE CASCADE,
FOREIGN KEY (service_id) REFERENCES service(service_id)
ON UPDATE CASCADE
);

INSERT INTO customer (`first_name`, `family_name`,email,phone) VALUES ('Shannon', 'Willis','shannon@willis.nz','0211661231');
INSERT INTO customer (`first_name`, `family_name`,email,phone) VALUES ('Simon', 'Chambers','simonchambers@gmail.com','033245678');
INSERT INTO customer (`first_name`, `family_name`,email,phone) VALUES ('Charles', 'Carmichael','carmichaels@hotmail.com','02754365286');
INSERT INTO customer (`first_name`, `family_name`,email,phone) VALUES ('Zhe', 'Wang','zhe.wang@qq.com','0743277893');
INSERT INTO customer (`first_name`, `family_name`,email,phone) VALUES ('Qi', 'Qi','qi@qi.co.nz','0294458423');
INSERT INTO customer (`family_name`,email,phone) VALUES ('Govindjee', 'hello@govindjee.nz','034156784');
INSERT INTO part (`part_name`, `cost`) VALUES ('Windscreen', '560.65');
INSERT INTO part (`part_name`, `cost`) VALUES ('Headlight', '35.65');
INSERT INTO part (`part_name`, `cost`) VALUES ('Wiper blade', '12.43');
INSERT INTO part (`part_name`, `cost`) VALUES ('Left fender', '260.76');
INSERT INTO part (`part_name`, `cost`) VALUES ('Right fender', '260.76');
INSERT INTO part (`part_name`, `cost`) VALUES ('Tail light', '120.54');
INSERT INTO part (`part_name`, `cost`) VALUES ('Hub Cap', '22.89');
INSERT INTO service (`service_name`, `cost`) VALUES ('Sandblast', '300.21');
INSERT INTO service (`service_name`, `cost`) VALUES ('Minor Fill', '43.21');
INSERT INTO service (`service_name`, `cost`) VALUES ('Major Fill', '125.70');
INSERT INTO service (`service_name`, `cost`) VALUES ('Respray', '800.33');
INSERT INTO service (`service_name`, `cost`) VALUES ('Touch up', '34.99');
INSERT INTO service (`service_name`, `cost`) VALUES ('Polish', '250.00');
INSERT INTO service (`service_name`, `cost`) VALUES ('Small Dent Removal', '49.99');
INSERT INTO service (`service_name`, `cost`) VALUES ('Large Dent Removal', '249.00');
INSERT INTO job (`job_date`, `customer`, `completed`, `paid`, total_cost) VALUES ('2023-11-01', '4', '1', '1', '410.22');
INSERT INTO job (`job_date`, `customer`) VALUES ('2024-02-02', '6');
INSERT INTO job (`job_date`, `customer`, `completed`) VALUES ('2023-12-11', '1', '1');
INSERT INTO job (`job_date`, `customer`) VALUES ('2023-12-12', '2');
INSERT INTO job (`job_date`, `customer`) VALUES ('2023-12-12', '5');
INSERT into job_part (job_id,part_id, qty) VALUES (1,2,2);
INSERT into job_part (job_id,part_id, qty) VALUES (1,4,1);
INSERT into job_service (job_id,service_id, qty) VALUES (1,2,1);
INSERT into job_service (job_id,service_id, qty) VALUES (1,5,1);

-- ============================================================================
-- User Authentication Table (Added in v2.0)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user
(
    user_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(320) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('technician', 'administrator') NOT NULL DEFAULT 'technician',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- Create default administrator account
-- Password should be changed on first login
-- Default password hash is for 'changeme' - MUST be changed in production
-- To generate a new hash: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_password'))"
INSERT INTO user (username, email, password_hash, role) VALUES
('admin', 'admin@autorepair.local', 'scrypt:32768:8:1$placeholder$changeme', 'administrator');

-- Note: The above password hash is a placeholder.
-- Run this SQL after application deployment to set a proper password:
-- UPDATE user SET password_hash = '<generated_hash>' WHERE username = 'admin';
