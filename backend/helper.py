from flask import jsonify


def build_success_response(data=None, msg='OK', errno=0):
    res = {
        'msg': msg,
        'errno': errno,
    }
    if data:
        res.update(data)
    return jsonify(res)


def build_error_response(data=None, msg='Error', errno=-1):
    res = {
        'msg': msg,
        'errno': errno
    }
    if data:
        res.update(data)

    return jsonify(res)


def not_modified(msg='not modified'):
    return build_error_response(msg=msg), 304


def bad_request(msg='bad request'):
    return build_error_response(msg=msg), 400


def unauthorized(msg='unauthorized'):
    return build_error_response(msg=msg), 401


def not_found(msg='not found'):
    return build_error_response(msg=msg), 404


def not_allowed(msg='method not allowed'):
    return build_error_response(msg=msg), 405


def precondition_failed(msg='precondition failed'):
    return build_error_response(msg=msg), 412


def internal_server_error(msg='internal server error'):
    return build_error_response(msg=msg), 500


def too_many_requests(msg='You have exceeded your request rate'):
    return build_error_response(msg=msg), 429
