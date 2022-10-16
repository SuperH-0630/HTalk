from flask import request, current_app
from flask_login import current_user


class Logger:
    @staticmethod
    def __get_log_request_info():
        return (f"user: '{current_user.email}' "
                f"url: '{request.url}' blueprint: '{request.blueprint}' "
                f"args: {request.args} form: {request.form} "
                f"accept_encodings: '{request.accept_encodings}' "
                f"accept_charsets: '{request.accept_charsets}' "
                f"accept_mimetypes: '{request.accept_mimetypes}' "
                f"accept_languages: '{request.accept_languages}'")

    @staticmethod
    def print_load_page_log(page: str):
        current_app.logger.debug(
            f"[{request.method}] Load - '{page}' " + Logger.__get_log_request_info())

    @staticmethod
    def print_form_error_log(opt: str):
        current_app.logger.warning(
            f"[{request.method}] '{opt}' - Bad form " + Logger.__get_log_request_info())

    @staticmethod
    def print_sys_opt_fail_log(opt: str):
        current_app.logger.error(
            f"[{request.method}] System {opt} - fail " + Logger.__get_log_request_info())

    @staticmethod
    def print_sys_opt_success_log(opt: str):
        current_app.logger.warning(
            f"[{request.method}] System {opt} - success " + Logger.__get_log_request_info())

    @staticmethod
    def print_user_opt_fail_log(opt: str):
        current_app.logger.debug(
            f"[{request.method}] User {opt} - fail " + Logger.__get_log_request_info())

    @staticmethod
    def print_user_opt_success_log(opt: str):
        current_app.logger.debug(
            f"[{request.method}] User {opt} - success " + Logger.__get_log_request_info())

    @staticmethod
    def print_user_opt_error_log(opt: str):
        current_app.logger.warning(
            f"[{request.method}] User {opt} - system fail " + Logger.__get_log_request_info())

    @staticmethod
    def print_import_user_opt_success_log(opt: str):
        current_app.logger.info(
            f"[{request.method}] User {opt} - success " + Logger.__get_log_request_info())

    @staticmethod
    def print_user_not_allow_opt_log(opt: str):
        current_app.logger.info(
            f"[{request.method}] User '{opt}' - reject " + Logger.__get_log_request_info())