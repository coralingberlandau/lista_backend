# Welcome to application LISTA - backend 👋



# To Do List:
    env - done

# Data base
    data.json - ??????

# Data structure

    1. MODEL 1: User - id, city, street, phone, image, user(Connection with 
    user MODEL)  = DONE -- ????

    2. MODEL 2: ListItem -id, city, street, phone, image, user_id(connection 
    with user model) =  = DONE

    3. MODEL 3: Product - id, product_type, price, description, image, 
    created_time = DONE

    4. MODEL 4: Cart - id, user_id(connection with user model), products_id
    (connection with products model), created_time = DONE

    5. MODEL 5: OrderDetail - id, cart_id(connection with cart model), 
    product_id(connection with products model), amount, total_price, 
    created_time = DONE

# Technologies

 - Frontend: Expo - Typescript --- React Native
 
 - Backend: Python with Django framework, CORS


# Status - CRUD

    ** not started \  in process \ done

    backend - DONE

    - backend:

    Customer - 
    Create (post) - done == > register
    Read all users (get)  - done
    Read whit id (get)  - done
    Update (put) - done
    Delete (del) - done 

    Product -  
    Create (post) - done
    Read (get)  - done
    Read whit id (get)  - done
    Update (put) - done
    Delete (del) - done

    Cart - 
    Create (post)  - done
    Read (get)   - done
    Update (put)  - done
    Delete (del)  - done

    OrderDetail - 
    Create (post)  - done
    Read (get)   - done
    Update (put)  - done
    Delete (del)  - done

    endpoint = register - done
    endpoint = login - done

# Begin:

1. Activate the virtual environment:
   - For macOS: `python3 -m virtualenv env` after to (לפהעיל את הסביבה הוירטואלית) `source env/bin/activate`
   - For other systems: `ython -m virtualenv env` after to (לפהעיל את הסביבה הוירטואלית) `env\Scripts\activate`

2. Install the requirements:
   - For macOS: `pip3 install -r requirements.txt`
   - For other systems: `pip install -r requirements.txt`

3. Run the program:
   - For macOS: `python3 manage.py runserver`
   - For other systems: `python manage.py runserver`

4. You can delete the data in the database file and 
write your own data from scratch. It will work.


        For improvements, suggestions, and 
        constructive feedback, I am always happy to 
        hear from you. Enjoy and good luck!
