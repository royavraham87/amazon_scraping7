# this Django file contain most of the fittures in Django exept for a picture.
# it contain login, register, the ability to add adition information on the token, rest_API and CORS.
# CRUD was generated with viewsets

### Future Plans:
Summary of Your Feature Plan:
1. Delete Products from Watchlist:
* Implement a delete button next to each product in the user's watchlist.
* Allow users to remove irrelevant products easily.

2. User Authentication:
* Integrate user login functionality with username, password, and email registration.
* Link user-specific watchlists and lists to authenticated accounts.

3. Multi-List Management:
* Allow users to create and name multiple lists to organize products.
* Implement the ability to add specific products to different lists.
* Add options to delete lists or rename them for better organization.

4. Automated Scraping Scheduler:
* Create a model to automatically scrape marked products at user-specified times (e.g., 09:30).
* Enable users to set up automated tracking schedules for their lists.

5. Graph Building for Price History:
* Develop a model that allows users to pick a product and view a graph of price changes over time.
* Integrate data visualization to make price trends clear and accessible.

6. Price Drop Alerts:
* Add an alert system to notify users via email when a product's price drops by at least 30% from the original price.
* Enhance user registration to include email for sending alerts.

7. Logging System:
* Implement a comprehensive logging system to track actions and errors for better debugging and monitoring.

8. Retry Mechanism:
* Integrate a retry mechanism for failed scraping requests to improve reliability against network issues and temporary site blocks.

9. Frontend Development:
* Create a user-friendly frontend interface to manage lists, add products, track products, schedule scrapes, and view data visualizations.
* Ensure seamless integration between the backend logic and the user interface.

What chat GPT Think:
This plan outlines a robust and feature-rich product that would greatly enhance the user experience. Here are my thoughts on how to proceed:

1. Frontend vs. Backend Development:
* Frontend: Given the complexity of user interaction required (e.g., managing lists, viewing graphs, and setting alerts), developing a simple frontend now would be beneficial. It would make testing features easier and provide users with a clear interface to manage their data.
* Backend: While you could continue developing backend functionality first, you may find it harder to test user-specific interactions and data management without some form of interface.

2. Priority Suggestions:
* Start with core backend features like user authentication, watchlist management, and automated scraping.
* Implement the logging and retry mechanism early to make development and debugging easier.
* Build a basic frontend once key backend features are in place, focusing on user interactions like login, product tracking, and list management.
* Gradually add more advanced features, such as graph building and alert systems, as you finalize core functionalities.

Balanced Approach:
* Consider building a minimal frontend while you continue backend development to allow for immediate feedback and iterative improvement.
* A simple frontend can serve as a test tool to validate backend features.

### commands:
celery -A scheduled_tasks worker --loglevel=info --pool=solo
python manage.py test_scheduled_scraping