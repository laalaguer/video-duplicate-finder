def seconds_to_str(total_seconds: int) -> str:
    ''' Convert time in seconds to HH:MM:SS format '''
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    time_formatted = "{:02}:{:02}:{:02}".format(hours, minutes, seconds)
    return time_formatted

def size_to_str(total_bytes: int) -> str:
    ''' Covert bytes into string representation of B/KB/MB/Gb/TB format'''
    one_kb = 1024
    one_mb = one_kb * 1024
    one_gb = one_mb * 1024
    one_tb = one_gb * 1024
    
    if total_bytes <= one_kb:
        return f'{total_bytes:4.1f}B'
    elif total_bytes > one_kb and total_bytes <= one_mb:
        v = total_bytes / one_kb
        return f'{v:4.1f}KB'
    elif total_bytes > one_mb and total_bytes <= one_gb:
        v = total_bytes / one_mb
        return f'{v:4.1f}MB'
    elif total_bytes > one_gb and total_bytes <= one_tb:
        v = total_bytes / one_gb
        return f'{v:4.1f}GB'
    else:
        v = total_bytes / one_tb
        return f'{v:4.1f}TB'