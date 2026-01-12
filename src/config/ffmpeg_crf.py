from src.config.main import Config


def get_video_crf():
    user_crf = getattr(Config.from_args().cli_options, 'crf', None)
    if user_crf == None:
        return "23" if Config.from_args().cli_options['video_codec'] == 'h264' else "28"
    return str(user_crf)
