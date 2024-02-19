import json
user_data = {}
def saving_user_data(user_data):
    user_data_copy = user_data.copy()
    for user_id, data in user_data_copy.items():
        data['sniped_classes'] = list(data['sniped_classes'])
    try:
        with open('user_data.json', 'w') as file:
            json.dump(user_data_copy, file, indent=4)
    except Exception as e:
        print(f"Error saving user data: {str(e)}")



def load_user_data():
    try:
        with open('user_data.json', 'r') as file:
            data = file.read()
            if data:
                return json.loads(data)
            else:
                return {}
    except FileNotFoundError:
        return{}
        

user_data = load_user_data()
