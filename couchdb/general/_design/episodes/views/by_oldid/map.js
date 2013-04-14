function(doc)
{
    if(doc.doc_type == "Episode")
    {
        if(doc.oldid)
        {
            emit(doc.oldid, null);
        }

        for(var n in doc.merged_oldids)
        {
            emit(doc.merged_oldids[n], null);
        }
    }
}
