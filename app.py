from flask import Flask , request , jsonify , make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash , check_password_hash
import jwt
import uuid
from datetime import datetime , timedelta
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer() , primary_key = True)
    public_id = db.Column(db.String(50) , unique = True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)


class Todo(db.Model):
    id = db.Column(db.Integer() , primary_key = True)
    text = db.Column(db.String(50))
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer)
    

def token_required(f):
    @wraps(f)
    def decorated(*args , **kwargs):

        token = request.headers.get('x-access-token')
        if token:
            
            data = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
            if current_user.admin:
                return f(*args,**kwargs)

        return jsonify({'message' : 'token is invalid'})

    return decorated





@app.route('/user' , methods = ['GET'])
@token_required
def get_all_user():

    users = User.query.all()

    output = []

    for user in users:
        user_data = {}
        user_data['pubilc_id'] = user.public_id
        user_data['name'] = user.name
        user_data['admin'] = user.admin

        output.append(user_data)

    return jsonify({'users':output})


@app.route('/user/<user_id>' , methods = ['GET'])
@token_required
def get_one_user(user_id):



    user = User.query.filter_by(public_id = user_id ).first()

    if user:
        user_data = {}
        user_data['pubilc_id'] = user.public_id
        user_data['name'] = user.name
        user_data['admin'] = user.admin
        
        return jsonify(user_data)

    return jsonify({'message':'user not found!'})



@app.route('/user/<user_id>' , methods=['PUT'])
@token_required
def promote_user(user_id):
    user = User.query.filter_by(public_id = user_id ).first()


    if user:
        user.admin  = True
        db.session.commit()
        return jsonify({'message':'user has been promoted to admin!.'})

    return jsonify({'message':'user not found!'})

@app.route('/user' , methods=['POST'])
@token_required
def create_user():

    data = request.get_json()

    hash_pass = generate_password_hash(data['password'] , method='sha256')


    public_id = str(uuid.uuid4())
    user = User(public_id = public_id , name=data['name'] , password = hash_pass , admin = False)

    db.session.add(user)
    db.session.commit()

    return jsonify({'message' : 'user added!'})



@app.route('/user/<user_id>' , methods=['DELETE'] )
@token_required
def delete_user(user_id):
    user = User.query.filter_by(public_id = user_id ).first()


    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message':'user has been deleted .'})

    

    return jsonify({'message':'user not found!'})


@app.route('/login' , methods=['POST'])

def login():

    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('could not verify' , 401 , {'WWW-Authenticate':'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('could not verify' , 401 , {'WWW-Authenticate':'Basic realm="Login required!"'})


    if check_password_hash(user.password , auth.password): 
        token = jwt.encode({'public_id' : user.public_id , 'exp' : datetime.now() + timedelta(minutes=30)} , app.config['SECRET_KEY'])
        return jsonify({ 'token':token })


    return make_response('could not verify' , 401 , {'WWW-Authenticate':'Basic realm="Login required!"'})








if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000 )