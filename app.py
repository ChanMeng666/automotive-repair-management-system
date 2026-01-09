"""
DEPRECATED: This file is deprecated and will be removed in a future version.
Please use 'run.py' as the application entry point instead.

This file is kept for backward compatibility only.
All new development should use the modular architecture in the 'app/' directory.
"""
import warnings
import os
from datetime import datetime
from flask import Flask, flash, render_template, request, redirect, url_for
import mysql.connector
import connect
import re

# Issue deprecation warning
warnings.warn(
    "app.py is deprecated. Please use 'run.py' instead. "
    "This file will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

app = Flask(__name__)

# Get secret key from environment variable (required for security)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-fallback-key')
if app.secret_key == 'dev-only-fallback-key':
    warnings.warn(
        "SECRET_KEY not set in environment. Using insecure default. "
        "Set SECRET_KEY environment variable for production!",
        UserWarning
    )

dbconn = None
connection = None

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(
        user=connect.dbuser,
        password=connect.dbpass,
        host=connect.dbhost,
        database=connect.dbname,
        autocommit=True
    )
    dbconn = connection.cursor(dictionary=True, buffered=True)
    return dbconn

# Function to calculate cost of service
def calculate_service_cost(service_id, qty):
    cursor = getCursor()
    cursor.execute(
        "SELECT cost FROM service WHERE service_id = %s", (service_id,)
    )
    data = cursor.fetchone()
    return data['cost'] * qty

# Function to calculate cost of part
def calculate_part_cost(part_id, qty):
    cursor = getCursor()
    cursor.execute(
        "SELECT cost FROM part WHERE part_id = %s", (part_id,)
    )
    data = cursor.fetchone()
    return data['cost'] * qty

# Function to update total cost of job
def update_total_cost(job_id):
    cursor = getCursor()

    # Calculate total cost of service
    cursor.execute(
        "SELECT SUM(js.qty * s.cost) AS service_total "
        "FROM job_service AS js JOIN service AS s ON js.service_id = s.service_id "
        "WHERE js.job_id = %s", [job_id]
    )
    service_total_data = cursor.fetchone()
    service_total = service_total_data['service_total'] if service_total_data and service_total_data['service_total'] else 0

    # Calculate total cost of parts
    cursor.execute(
        "SELECT SUM(jp.qty * p.cost) AS part_total "
        "FROM job_part AS jp JOIN part AS p ON jp.part_id = p.part_id "
        "WHERE jp.job_id = %s", [job_id]
    )
    part_total_data = cursor.fetchone()
    part_total = part_total_data['part_total'] if part_total_data and part_total_data['part_total'] else 0

    # Update total_cost in job table
    new_total_cost = service_total + part_total
    cursor.execute(
        "UPDATE job SET total_cost = %s WHERE job_id = %s",
        (new_total_cost, job_id)
    )
    connection.commit()

# Define the home route and function
@app.route("/")
def home():
    return render_template('base.html')

# Define the currentjoblist page route and function
@app.route("/currentjoblist", methods=['GET', 'POST'])
def currentjoblist():
    # Retrieve paginated jobs
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    cursor = getCursor()
    cursor.execute(
        "SELECT c.customer_id, c.first_name, c.family_name, j.job_id, j.job_date, j.total_cost, j.completed, j.paid "
        "FROM customer AS c JOIN job AS j ON c.customer_id = j.customer "
        "WHERE j.completed = 0 "
        "ORDER BY c.first_name, c.family_name, j.job_date DESC "
        "LIMIT %s OFFSET %s", (per_page, offset)
    )
    data = cursor.fetchall()

    # Handle POST request and redirect to modify job page
    if request.method == 'POST':
        jobid = request.form.get('job_select')

        if not jobid:
            return render_template('currentjoblist.html', data=data, message="Please select a job before modify.")
        return redirect(url_for('modifyjob', job_id=jobid))

    return render_template('currentjoblist.html', data=data, page=page)

# Define job modification page route and function
@app.route("/job/<int:job_id>", methods=['GET', 'POST'])
def modifyjob(job_id):
    cursor = getCursor()

    # Reports, services and parts for the job
    cursor.execute(
        "SELECT c.customer_id, c.first_name, c.family_name, j.job_id, j.job_date, j.total_cost, j.completed, j.paid "
        "FROM customer AS c JOIN job AS j ON c.customer_id = j.customer "
        "WHERE j.job_id= %s", (job_id,)
    )
    job_data = cursor.fetchone()

    cursor.execute(
        "SELECT s.service_name, js.qty "
        "FROM service AS s JOIN job_service AS js ON s.service_id = js.service_id "
        "WHERE js.job_id= %s ORDER BY s.service_name", (job_id,)
    )
    services_data = cursor.fetchall()

    cursor.execute(
        "SELECT p.part_name, jp.qty "
        "FROM part AS p JOIN job_part AS jp ON p.part_id = jp.part_id "
        "WHERE jp.job_id= %s ORDER BY p.part_name ", (job_id,)
    )
    parts_data = cursor.fetchall()

    # Fetch all services and parts
    cursor.execute("SELECT * FROM service ORDER BY service_name")
    all_services_data = cursor.fetchall()

    cursor.execute("SELECT * FROM part ORDER BY part_name")
    all_parts_data = cursor.fetchall()

    job_completed = True if job_data['completed'] else False

    return render_template('technician_modify_job.html', data=job_data, services=services_data, parts=parts_data, all_services=all_services_data, all_parts=all_parts_data, job_completed=job_completed)

# Add service to the job
@app.route("/add_service_to_job/<int:job_id>", methods=['POST'])
def add_service_to_job(job_id):
    service_id = request.form.get('service_id')
    qty = request.form.get('service_qty')

    # Calculate service cost
    service_cost = calculate_service_cost(service_id, int(qty))

    cursor = getCursor()

    # Update job's total_cost
    cursor.execute(
        "UPDATE job SET total_cost = total_cost + %s WHERE job_id = %s",
        (service_cost, job_id)
    )
    # Insert service into job_service table
    cursor.execute(
        "INSERT INTO job_service (job_id, service_id, qty) VALUES (%s, %s, %s)",
        (job_id, service_id, qty)
    )
    connection.commit()
    update_total_cost(job_id)

    return redirect(url_for('modifyjob', job_id=job_id))

# Add part to the job
@app.route("/add_part_to_job/<int:job_id>", methods=['POST'])
def add_part_to_job(job_id):
    part_id = request.form.get('part_id')
    qty = request.form.get('part_qty')

    # Calculate part cost
    part_cost = calculate_part_cost(part_id, int(qty))

    cursor = getCursor()

    # Update job's total_cost
    cursor.execute(
        "UPDATE job SET total_cost = total_cost + %s WHERE job_id = %s",
        (part_cost, job_id)
    )

    # Insert part into job_part table
    cursor.execute(
        "INSERT INTO job_part (job_id, part_id, qty) VALUES (%s, %s, %s)",
        (job_id, part_id, qty)
    )

    connection.commit()
    update_total_cost(job_id)

    return redirect(url_for('modifyjob', job_id=job_id))

#  Marking a job as completed
@app.route("/job/<int:job_id>/mark_as_completed", methods=['POST'])
def mark_job_as_completed(job_id):
    cursor = getCursor()
    cursor.execute(
        "UPDATE job SET completed=1 WHERE job_id = %s",
        (job_id,)
    )

    # Display flash message for marking as completed
    flash('Job marked as completed!', 'info')

    return redirect(url_for('modifyjob', job_id=job_id))


# Route and function for administrator_customer_list page
@app.route("/administrator_customer_list", methods=['POST', 'GET'])
def administrator_customer_list():
    cursor = getCursor()

    if request.method == 'POST':
        customer_id = request.form.get('customer_select')
        job_date = request.form.get('job_date')

        if customer_id and job_date:
            # Insert a new job entity related to the selected customer with specified date
            cursor.execute(
                "INSERT INTO job (job_date, customer, completed, paid, total_cost) "
                "VALUES (%s, %s, %s, %s, %s)",
                (job_date, customer_id, 0, 0, 0.00)
            )

        elif 'customer_search' in request.form and 'search_text' in request.form:
            # Search for customers by first name or family name
            search_option = request.form.get('customer_search')
            search_text = request.form.get('search_text')

            if search_option == 'first_name':
                cursor.execute(
                    "SELECT * FROM customer WHERE first_name LIKE %s",
                    ("%" + search_text + "%",)
                )
            elif search_option == 'family_name':
                cursor.execute(
                    "SELECT * FROM customer WHERE family_name LIKE %s",
                    ("%" + search_text + "%",)
                )
            else:
                cursor.execute("SELECT * FROM customer ORDER BY family_name, first_name")

        else:
            cursor.execute("SELECT * FROM customer ORDER BY family_name, first_name")

    else:
        cursor.execute("SELECT * FROM customer ORDER BY family_name, first_name")

    customers = cursor.fetchall()

    cursor.execute("SELECT * FROM service ORDER BY service_name")
    services = cursor.fetchall()

    cursor.execute("SELECT * FROM part ORDER BY part_name")
    parts = cursor.fetchall()

    # SQL statement to simultaneously fetch customer and job data, preventing SQL injection
    sql = ("SELECT customer.customer_id, customer.first_name, customer.family_name, "
           "job.job_id, job.job_date, job.total_cost, job.completed, job.paid "
           "FROM job INNER JOIN customer ON job.customer = customer.customer_id "
           "ORDER BY customer.family_name, customer.first_name")
    cursor.execute(sql)

    jobs = cursor.fetchall()


    return render_template('administrator_customer_list.html', customers=customers, services=services, parts=parts, jobs=jobs)


@app.route("/schedule_job", methods=['POST'])
def schedule_job():
    cursor = getCursor()
    customer_id = request.form.get('customer_select')
    job_date = request.form.get('job_date')
    # Insert a new job entity related to the selected customer with specified date
    cursor.execute(
        "INSERT INTO job (job_date, customer, completed, paid, total_cost) "
        "VALUES (%s, %s, %s, %s, %s)",
        (job_date, customer_id, 0, 0, 0.00)
    )
    return redirect(url_for('administrator_customer_list'))



# Route and function for adding a customer
@app.route("/add_customer", methods=['POST'])
def add_customer():
    cursor = getCursor()
    first_name = request.form.get('first_name', default=None)
    family_name = request.form.get('family_name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    # Insert a new customer entity
    cursor.execute(
        "INSERT INTO customer (first_name, family_name, email, phone) "
        "VALUES (%s, %s, %s, %s)",
        (first_name, family_name, email, phone)
    )

    return redirect(url_for('administrator_customer_list'))


# Route and function for adding a service
@app.route("/add_service", methods=['POST'])
def add_service():
    cursor = getCursor()
    service_name = request.form.get('service_name', default=None)
    service_cost = request.form.get('service_cost')

    # Insert a new service entity
    cursor.execute(
        "INSERT INTO service (service_name, cost) "
        "VALUES (%s, %s)",
        (service_name, service_cost)
    )

    return redirect(url_for('administrator_customer_list'))


# Route and function for adding a part
@app.route("/add_part", methods=['POST'])
def add_part():
    cursor = getCursor()
    part_name = request.form.get('part_name', default=None)
    part_cost = request.form.get('part_cost')

    # Insert a new part entity
    cursor.execute(
        "INSERT INTO part (part_name, cost) "
        "VALUES (%s, %s)",
        (part_name, part_cost)
    )

    return redirect(url_for('administrator_customer_list'))


# Route and function for administrator_pay_bills page
@app.route("/administrator_pay_bills", methods=['GET', 'POST'])
def administrator_pay_bills():
    cursor = getCursor()

    if request.method == 'POST':
        selected_customer = request.form["selected_customer"]

        if selected_customer != 'Choose...':
            cursor.execute("""
                SELECT job.job_id, job.job_date, job.total_cost, job.completed, job.paid, 
                       customer.customer_id, customer.first_name, customer.family_name
                FROM job
                JOIN customer ON job.customer = customer.customer_id
                WHERE job.paid = 0 
                      AND CONCAT(customer.first_name, ' ', customer.family_name) = %s
                ORDER BY customer.family_name, customer.first_name
            """, (selected_customer,))

        else:
            cursor.execute("""
                SELECT job.job_id, job.job_date, job.total_cost, job.completed, job.paid, 
                       customer.customer_id, customer.first_name, customer.family_name
                FROM job
                JOIN customer ON job.customer = customer.customer_id
                WHERE job.paid = 0
                ORDER BY customer.family_name, customer.first_name
            """)

        customer_info = cursor.fetchall()

    else:
        cursor.execute("""
            SELECT job.job_id, job.job_date, job.total_cost, job.completed, job.paid, 
                   customer.customer_id, customer.first_name, customer.family_name
            FROM job
            JOIN customer ON job.customer = customer.customer_id
            WHERE job.paid = 0
            ORDER BY customer.family_name, customer.first_name
        """)

        customer_info = cursor.fetchall()

    cursor.execute("""
        SELECT CONCAT(IFNULL(first_name,''), ' ', family_name) AS full_name 
        FROM customer 
        ORDER BY family_name, first_name
    """)

    all_customers = cursor.fetchall()

    return render_template('administrator_pay_bills.html',
                           customer_info=customer_info,
                           customers=all_customers)


# Route and function for marking a job as paid
@app.route("/administrator_mark_paid", methods=['POST'])
def administrator_mark_paid():
    cursor = getCursor()
    customer_id = request.form["bill_select"]

    cursor.execute("UPDATE job SET paid = 1 WHERE customer = %s", (customer_id,))

    flash("The selected bill is marked as paid.")
    return redirect(url_for("administrator_pay_bills"))


@app.route("/administrator_overdue_bills", methods=['GET', 'POST'])
def administrator_overdue_bills():
    cursor = getCursor()
    customer_data = None
    selected_customer = None
    customer_id_name = None
    job_data = None

    if request.method == 'POST':
        customer_id_name = request.form.get('customer_choose_overduebill')
    elif request.method == 'GET':
        # Get information about the first customer. If the database is empty, this statement will throw an exception.
        cursor.execute("""
            SELECT customer_id, first_name, family_name
            FROM customer
            ORDER BY family_name, first_name
            LIMIT 1
        """)
        customer = cursor.fetchone()
        customer_id_name = f'{customer["customer_id"]} {customer["first_name"]} {customer["family_name"]}'

    if 'Show all bills...' in customer_id_name:  # if 'Show all bills...' option is selected
        selected_customer = None
    else:
        customer_id = int(customer_id_name.split(' ')[0])  # assume the customer id is the first part of the option value
        # Fixed: Use parameterized query to prevent SQL injection
        cursor.execute("""
            SELECT customer_id, first_name, family_name, email, phone
            FROM customer
            WHERE customer_id = %s
        """, (customer_id,))
        result = cursor.fetchall()
        selected_customer = result[0] if result else None

    cursor.execute("""
        SELECT customer_id, first_name, family_name
        FROM customer
        ORDER BY family_name, first_name
    """)
    customer_data = cursor.fetchall()

    cursor.execute("""
        SELECT job.job_id, job.job_date, job.total_cost, job.completed, job.paid, 
               customer.customer_id, customer.first_name, customer.family_name
        FROM job
        JOIN customer ON job.customer = customer.customer_id
        ORDER BY job.job_date
    """)
    job_data = cursor.fetchall()

    now = datetime.now().date()
    for job in job_data:
        job['overdue'] = (now - job['job_date']).days > 14 and job['paid'] == 0

    return render_template('administrator_overdue_bills.html', jobs=job_data, customers=customer_data,
                           selected_customer=selected_customer)


# Main function to initiate the application on local server
if __name__ == "__main__":
    app.run(debug=True)