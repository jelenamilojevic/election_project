class Configuration():
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost/elections"
    REDIS_HOST = "localhost"
    REDIS_VOTES_LIST = "votes"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"