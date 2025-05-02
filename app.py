from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "key"

# SQLAlchemy config
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/blood_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
db = SQLAlchemy(app)  

# Donor Model
class Donor(db.Model):
    donor_id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(100), nullable=False)
    last = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100))
    phone_number = db.Column(db.String(15))
    blood_type = db.Column(db.String(5))


# Home Page Route
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        donors = Donor.query.all()

        # List of all possible blood types
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

        # Fetch distinct countries dynamically from donor table
        countries = db.session.query(Donor.country).distinct().all()
        countries = [c[0] for c in countries]  

        # Default values for stored procedure parameters
        selected_blood_type = request.form.get("blood_type", None)
        selected_country = request.form.get("country", None)

        # Call stored procedure with selected filters 
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        print(selected_blood_type)
        print(selected_country)
        cursor.callproc("compatible_blood", [selected_blood_type, selected_country])
        cursor.execute("SELECT * FROM compatible_donors")
        compatible_donors = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()

        return render_template(
            'index.html',
            donors=donors,
            compatible_donors=compatible_donors,
            blood_types=blood_types,
            countries=countries,
            selected_blood_type=selected_blood_type,
            selected_country=selected_country
        )

    except Exception as e:
        return f"Database error: {e}"

# Route to handle form submission and update donor info
@app.route('/edit_donor_form/<int:donor_id>', methods=['GET', 'POST'])
def edit_donor_form(donor_id):
    donor = Donor.query.get(donor_id)

    if request.method == 'POST':
        # Update the donor's details
        donor.first = request.form['first']
        donor.last = request.form['last']
        donor.country = request.form['country']
        donor.phone_number = request.form['phone_number']
        donor.blood_type = request.form['blood_type']

        try:
            db.session.commit()
            flash("Donor updated successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error updating donor: {e}", "danger")
            db.session.rollback()

    return render_template('edit_donor_form.html', donor=donor)


# Add Donor Route
@app.route('/add_donor', methods=['GET', 'POST'])
def add_donor():
    if request.method == 'POST':
        first = request.form['first']
        last = request.form['last']
        country = request.form['country']
        phone_number = request.form['phone_number']
        blood_type = request.form['blood_type']

        try:
            # Using SQLAlchemy ORM to add a new donor
            new_donor = Donor(first=first, last=last, country=country, phone_number=phone_number, blood_type=blood_type)
            db.session.add(new_donor)
            db.session.commit()
            flash("Donor added successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Database error: {e}", "danger")

    return render_template('add_donor.html')

# Show the Delete Donor Page
@app.route('/delete_donor/<int:donor_id>', methods=['POST'])
def delete_donor(donor_id):
    try:
        # Connect to the database using SQLAlchemy connection
        conn = db.engine.raw_connection()
        cursor = conn.cursor()

        # Call the stored procedure to delete the donor by donor_id
        cursor.callproc('DeleteDonor', [donor_id])

        # Commit the transaction to ensure the delete is done
        conn.commit()
        flash("Donor deleted successfully!", "success")

    except Exception as e:
        flash(f"Database error: {e}", "danger")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))  # Redirect back to the main page



if __name__ == '__main__':
    app.run(debug=True)
