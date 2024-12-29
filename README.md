<div align="center">
 <h1><img src="public/selwyn-panel-beaters-online.svg" width="80px"><br/>Selwyn Panel Beaters Online Service</h1>
 <img src="https://img.shields.io/badge/python-3.9+-blue?style=flat&logo=python&logoColor=white"/>
 <img src="https://img.shields.io/badge/Flask-3.0.1-black?style=flat&logo=flask&logoColor=white"/>
 <img src="https://img.shields.io/badge/MySQL-8.3.0-blue?style=flat&logo=mysql&logoColor=white"/>
 <img src="https://img.shields.io/badge/Bootstrap-5.0-purple?style=flat&logo=bootstrap&logoColor=white"/>
 <img src="https://img.shields.io/badge/License-MIT-brightgreen?style=flat"/>
</div>


https://github.com/user-attachments/assets/10dc2190-187c-4c52-bbbb-a3a0e4436005


![screencapture-chanmeng-pythonanywhere-2024-12-07-14_58_47](https://github.com/user-attachments/assets/fc5e01b6-380d-492d-9961-68c3d1f0dfff)

![屏幕截图 2024-12-07 150003](https://github.com/user-attachments/assets/b5d1eec3-88db-45ed-aaea-74c1bc8dfb13)

![screencapture-chanmeng-pythonanywhere-currentjoblist-2024-12-07-14_59_06](https://github.com/user-attachments/assets/8ec92d9a-c896-4471-9a60-3af579c57875)

# Features
The Selwyn Panel Beaters Online Service provides a comprehensive solution for automotive repair shop management with dedicated interfaces for technicians and administrators.

### 🔧 Technician Interface
- View and manage current repair jobs
- Add services and parts to jobs
- Track job completion status
- Real-time cost calculation
- User-friendly job modification interface

### 👥 Administrator Interface
- Manage customer information and records
- Schedule new repair jobs
- Track unpaid bills and payments
- Monitor overdue accounts
- Add/update services and parts catalog
- Comprehensive billing management

### 💼 Business Management
- Automated cost calculation
- Job status tracking
- Payment status monitoring
- Customer information management
- Parts and services inventory
- Billing and payment processing

### 🛠️ System Features
- Intuitive user interfaces
- Responsive design
- Real-time updates
- Secure data management
- Multi-user support
- Automated calculations

## Tech Stack
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/python-%2314354C.svg?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge&logo=mysql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/bootstrap-%23563D7C.svg?style=for-the-badge&logo=bootstrap&logoColor=white)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)

## Getting Started

### Prerequisites
- Python 3.9+
- MySQL 8.0+
- Web browser with JavaScript enabled

### Installation
1. Clone the repository
```bash
git clone https://github.com/ChanMeng666/automotive-repair-management-system.git
```

2. Install required packages
```bash
pip install -r requirements.txt
```

3. Set up MySQL database
```bash
mysql -u root -p < spb_local.sql
```

4. Configure database connection
Update the `connect.py` file with your MySQL credentials.

5. Run the application
```bash
python app.py
```

The application will be accessible at `http://localhost:5000`.

## Database Schema

The system uses a MySQL database with the following main tables:
- `customer`: Stores customer information
- `job`: Manages repair jobs
- `service`: Catalogs available services
- `part`: Tracks parts inventory
- `job_service`: Links jobs with services
- `job_part`: Links jobs with parts

## Contributing
Contributions are welcome! Please read our [Contributing Guidelines](CODE_OF_CONDUCT.md) for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
Email: ChanMeng666@outlook.com

## 🙋‍♀ Author

Created and maintained by [Chan Meng](https://github.com/ChanMeng666).

## Acknowledgments
Special thanks to everyone who has contributed to making this project better.

- Bootstrap Documentation
- Flask Documentation
- MySQL Documentation
