# Finance Tracker
## Project Purpose
>This project was a personal project to expand my knowledge of web development and Python programming. I added to my limited JavaScript knowledge by learning how JS modules worked and how I could use one of them (Chart.js) to visualize graphs and pie charts dynamically. As I'm only 15 and entering my first year of high school, for me going the extra mile is worth it because it's unlocking a passion for not only computer science and its branches but also learning as a whole and what it means to be a lifelong student. I hope to continue learning about how technology influences the world and how we can use it to make science fiction a reality. 

>CS, python, flask, flask web framework, web development, CS50
## Features
I've used Flask web framework based in Python
its was necessary flask-sqlalchemy for manage SQL database with sqlite and flask-wtf for upload files and forms extensions
Plus I used csv files to keep track of all the transactions users made
## Explaining the project

The Finance Tracker is a comprehensive program designed to help individuals and small businesses manage their financial transactions efficiently. It allows users to record, categorize, and analyze their income and expenses, providing valuable insights into their financial health. Each transaction includes essential information such as transaction type (income or expense), category (e.g., Salary, Rent, Groceries), and amount. Users can easily input new transactions and categorize them for better organization. 

In addition to transaction management, the Finance Tracker offers robust reporting and analysis tools. Users can view summaries of their total income and expenses, along with a breakdown of expenses by category to identify spending patterns and potential savings. The program calculates the net balance by subtracting total expenses from total income, giving users a clear picture of their financial standing. With its user-friendly interface and essential features, the Finance Tracker empowers individuals and small businesses to make informed financial decisions and maintain a healthy financial balance.

### Databases
I needed 2 tables for my database:

- First, table users. Where I put, id, email, password_hash, notice that id must be a primary key here.

- Second,  balances. It stored for every user a balance that contaied the user_id, current balance, saving balance, and what currency the program was based on.

I also used csv files to track users transactions. each unique by their user_id

## Thank you note:

This project taught me a lot, from new libraries and coding skills to practical skills like dealing with new errors. I owe all my computer science and coding knowledge to organizations and people who are kind enough to put free courses online. I have completed CS50X and CS50P and am in the process of taking CS50AI (the most challenging yet). So a sincere thank you to the CS50 Harvard group, all the Stackoverflow users and everyone who makes an effort to make learning to code more engaging and easier every day.
