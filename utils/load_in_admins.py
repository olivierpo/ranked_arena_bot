def load_in_admins():
    global_admin_list = [118201449392898052, 242753760890191884]
    with open("../admin_list.txt", "r") as readfile:
        for admins in readfile:
            global_admin_list.append(int(admins[:-1]))
    return global_admin_list

