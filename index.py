# api/index.py

def handler(request):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/plain"},
        "body": "Hello! Your Vercel Python function is working 🚀"
    }