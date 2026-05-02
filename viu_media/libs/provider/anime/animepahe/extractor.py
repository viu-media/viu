import re


def animepahe_key_creator(c: int, a: int):
    from ...scraping.utils import encode_base_n

    if c < a:
        val_a = ""
    else:
        val_a = animepahe_key_creator(int(c / a), a)
    c = c % a
    if c > 35:
        val_b = chr(c + 29)
    else:
        val_b = encode_base_n(c, 36)
    return val_a + val_b


def animepahe_embed_decoder(
    encoded_js_p: str,
    base_a: int,
    no_of_keys_c: int,
    values_to_replace_with_k: list,
):
    decode_mapper_d: dict = {}
    for i in range(no_of_keys_c):
        key = animepahe_key_creator(i, base_a)
        val = values_to_replace_with_k[i] or key
        decode_mapper_d[key] = val
    return re.sub(
        r"\b\w+\b", lambda match: decode_mapper_d[match.group(0)], encoded_js_p
    )


PARAMETERS_REGEX = re.compile(r"eval\(function\(p,a,c,k,e,d\)\{.*\}\((.*?)\)\)$")
ENCODE_JS_REGEX = re.compile(r"'(.*?);',(\d+),(\d+),'(.*)'\.split")


def process_animepahe_embed_page(embed_page: str):
    from ...scraping.html_parser import get_element_text_and_html_by_tag

    encoded_js_string = ""
    embed_page_content = embed_page
    for _ in range(8):
        text, html = get_element_text_and_html_by_tag("script", embed_page_content)
        if not text and html:
            embed_page_content = re.sub(html, "", embed_page_content)
            continue
        if text:
            encoded_js_string = text.strip()
            break
    if not encoded_js_string:
        return
    obsfucated_js_parameter_match = PARAMETERS_REGEX.search(encoded_js_string)
    if not obsfucated_js_parameter_match:
        return
    parameter_string = obsfucated_js_parameter_match.group(1)
    encoded_js_parameter_string = ENCODE_JS_REGEX.search(parameter_string)
    if not encoded_js_parameter_string:
        return
    p: str = encoded_js_parameter_string.group(1)
    a: int = int(encoded_js_parameter_string.group(2))
    c: int = int(encoded_js_parameter_string.group(3))
    k: list = encoded_js_parameter_string.group(4).split("|")
    return animepahe_embed_decoder(p, a, c, k).replace("\\", "")


if __name__ == "__main__":
    # Testing time
    filepath = input("Enter file name: ")
    if filepath:
        with open(filepath) as file:
            data = file.read()
    else:
        data = """<script>eval(function(p,a,c,k,e,d){e=function(c){return(c<a?'':e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--){d[e(c)]=k[c]||e(c)}k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1};while(c--){if(k[c]){p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c])}}return p}('f $7={H:a(2){4 B(9.7.h(y z("(?:(?:^|.*;)\\\\s*"+d(2).h(/[\\-\\.\\+\\*]/g,"\\\\$&")+"\\\\s*\\\\=\\\\s*([^;]*).*$)|^.*$"),"$1"))||G},E:a(2,q,3,6,5,t){k(!2||/^(?:8|r\\-v|o|m|p)$/i.D(2)){4 w}f b="";k(3){F(3.J){j K:b=3===P?"; 8=O, I N Q M:u:u A":"; r-v="+3;n;j L:b="; 8="+3;n;j S:b="; 8="+3.Z();n}}9.7=d(2)+"="+d(q)+b+(5?"; m="+5:"")+(6?"; o="+6:"")+(t?"; p":"");4 x},Y:a(2,6,5){k(!2||!11.C(2)){4 w}9.7=d(2)+"=; 8=12, R 10 W l:l:l A"+(5?"; m="+5:"")+(6?"; o="+6:"");4 x},C:a(2){4(y z("(?:^|;\\\\s*)"+d(2).h(/[\\-\\.\\+\\*]/g,"\\\\$&")+"\\\\s*\\\\=")).D(9.7)},X:a(){f c=9.7.h(/((?:^|\\s*;)[^\\=]+)(?=;|$)|^\\s*|\\s*(?:\\=[^;]*)?(?:\\1|$)/g,"").T(/\\s*(?:\\=[^;]*)?;\\s*/);U(f e=0;e<c.V;e++){c[e]=B(c[e])}4 c}};',62,65,'||sKey|vEnd|return|sDomain|sPath|cookie|expires|document|function|sExpires|aKeys|encodeURIComponent|nIdx|var||replace||case|if|00|domain|break|path|secure|sValue|max||bSecure|59|age|false|true|new|RegExp|GMT|decodeURIComponent|hasItem|test|setItem|switch|null|getItem|31|constructor|Number|String|23|Dec|Fri|Infinity|9999|01|Date|split|for|length|1970|keys|removeItem|toUTCString|Jan|this|Thu'.split('|'),0,{}));eval(function(p,a,c,k,e,d){e=function(c){return(c<a?'':e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--){d[e(c)]=k[c]||e(c)}k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1};while(c--){if(k[c]){p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c])}}return p}('h o=\'1D://1C-E.1B.1A.1z/1y/E/1x/1w/1v.1u\';h d=s.r(\'d\');h 0=B 1t(d,{\'1s\':{\'1r\':i},\'1q\':\'16:9\',\'D\':1,\'1p\':5,\'1o\':{\'1n\':\'1m\'},1l:[\'7-1k\',\'7\',\'1j\',\'1i-1h\',\'1g\',\'1f-1e\',\'1d\',\'D\',\'1c\',\'1b\',\'1a\',\'19\',\'C\',\'18\'],\'C\':{\'17\':i}});8(!A.15()){d.14=o}x{j z={13:12,11:10,Z:Y,X:i,W:i};h c=B A(z);c.V(o);c.U(d);g.c=c}0.3("T",6=>{g.S.R.Q("P")});0.O=1;k v(b,n,m){8(b.y){b.y(n,m,N)}x 8(b.w){b.w(\'3\'+n,m)}}j 4=k(l){g.M.L(l,\'*\')};v(g,\'l\',k(e){j a=e.a;8(a===\'7\')0.7();8(a===\'f\')0.f();8(a===\'u\')0.u()});0.3(\'t\',6=>{4(\'t\')});0.3(\'7\',6=>{4(\'7\')});0.3(\'f\',6=>{4(\'f\')});0.3(\'K\',6=>{4(0.q);s.r(\'.J-I\').H=G(0.q.F(2))});0.3(\'p\',6=>{4(\'p\')});',62,102,'player|||on|sendMessage||event|play|if||data|element|hls|video||pause|window|const|true|var|function|message|eventHandler|eventName|source|ended|currentTime|querySelector|document|ready|stop|bindEvent|attachEvent|else|addEventListener|config|Hls|new|fullscreen|volume|01|toFixed|String|innerHTML|timestamp|ss|timeupdate|postMessage|parent|false|speed|landscape|lock|orientation|screen|enterfullscreen|attachMedia|loadSource|lowLatencyMode|enableWorker|Infinity|backBufferLength|600|maxMaxBufferLength|180|maxBufferLength|src|isSupported||iosNative|capture|airplay|pip|settings|captions|mute|time|current|progress|forward|fast|rewind|large|controls|kwik|key|storage|seekTime|ratio|global|keyboard|Plyr|m3u8|uwu|b92a392054c041a3f9c6eecabeb0e127183f44e547828447b10bca8d77523e6f|03|stream|org|nextcdn|files|eu|https'.split('|'),0,{}))</script>"""

    print(process_animepahe_embed_page(data))
