# UMA App

This is a sample application to demonstrate a UMA Resource Server
and requesting party using oxd.

## Files

* `rs.py` - A simple flask application
* `rs.cfg` - oxd-python config file for the flask application

## Demo Application

### What does the app do?

* The app acts as a UMA Resource server.
* It provides an interface to ask the Authorization Server to
protect two resource end points `/resource/photos/` and `/resource/docs/`.
* Once the endpoints are protected with required *Scopes* and *Http Methods*, they can be accessed to verify the protection.
* When either of the endpoints `/resource/photos/` or `/resource/docs` is accessed, it asks the AS for validity and returns a response based on the Auth Server's answer.

### Prerequisites

* A Gluu Server to act as the Authorization Server. Use this server's URL
as `op_host` in the configuration `rs.cfg`
* oxd-server or oxd-https-extension

### Running the app

```
git clone https://github.com/GluuFederation/oxd-python.git
cd oxd-python
python setup.py install
pip install flask pyOpenSSL
cd examples/uma_rs/

# Edit the rs.cfg to suit your op_host
# remove the line with oxd_id if present

# run the application
python rs.py
```

Now the RS site should be available at `https://localhost:8085`

### Endpoints

-----------------------------------------------------
|  Endpoint  | Methods           | Description      |
|------------|-------------------|------------------|
| `/`        | GET               | Home page of the application |
| `/protect` | POST              | URL where the form is submitted from the homepage for resource protection. |
| `/resource/<resource>/` | GET, POST, PUT, DELETE | API for accessing and the resource. Use a REST client |
| `/rp/get_rpt/`| GET            | A utility endpoint to get RPT as an UMA Requesting Party. |
-------------------------------------------------------------


### Typical Resource Protection & Access Cycle

#### Resource Protection

1. With the `python rs.py` running, open `https://localhost:8085`
2. Select the resource, scope and http method and protect the resource.
   Assume **resource** is `Photos`, **scope** is `View` and the **http method** is `GET` as an example.

#### Resource Access

**Note:** Ideally all this should be done by a separate UMA Requesting Party App. For the RS example, lets just use `cURL`

1. Access the URL `https://localhost:8085/resources/photos/` from a REST client.
```
$ curl -k https://localhost:8085/resource/photos/
{
  "access": "denied",
  "ticket": "030db88e-f07f-4558-bd17-3ac2a7400be3",
  "www-authenticate_header": "UMA realm=\"rs\",as_uri=\"https://gluu.example.com\",error=\"insufficient_scope\",ticket=\"030db88e-f07f-4558-bd17-3ac2a7400be3\""
}
```
2. Use the Requesting Party utility URL to generate RPT Token.
```
$ curl -k https://localhost:8085/rp/get_rpt/?ticket=030db88e-f07f-4558-bd17-3ac2a7400be3
{
  "access_token": "ebe71635-1c24-470c-830c-7bc961e33457_140A.BA5B.556E.9842.0E8F.EFF7.F0AF.12E9",
  "pct": "ed0ce518-ebfd-41ae-b3a6-c6a6a9d8f440_5F41.AB57.0892.31D3.D786.CFB4.CF9D.D32C",
  "token_type": "Bearer",
  "updated": false
}
```
3. Now access the resource with the RPT access token
```
curl -k -H 'Authorization: Bearer ebe71635-1c24-470c-830c-7bc961e33457_140A.BA5B.556E.9842.0E8F.EFF7.F0AF.12E9' https://localhost:8085/resource/photos/
{
  "resource": "photos",
  "type": "image",
  "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Tamil_Nadu_Literacy_Map_2011.png"
}
```
Voila here is our resource.

Happy building UMA apps with oxd-python.