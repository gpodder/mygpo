function(doc)
{
    if(doc.doc_type == "Episode")
    {
        emit(doc._id, null);

        for(var n in doc.merged_ids)
        {
            emit(doc.merged_ids[n], null);
        }
    }
}
