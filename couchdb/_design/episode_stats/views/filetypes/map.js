function(doc)
{
    if(doc.doc_type == "Episode")
    {
        for(var n in doc.urls)
        {
            var url = doc.urls[n];
            var i = url.lastIndexOf(".");

            if(i >= 0)
            {
                /* exclude the dot */
                var ext = url.substr(i+1);

                /* make sure we exclude obvious non-extensions */
                if (ext.length < 10)
                {
                    emit(ext, url);
                }
            }
        }
    }
}
