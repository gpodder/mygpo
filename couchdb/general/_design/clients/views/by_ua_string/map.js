function(doc)
{
    if(doc.doc_type == "User")
    {
        for(var n in doc.devices)
        {
            var device = doc.devices[n];
            if(device.user_agent)
            {
                emit(device.user_agent, device.id);
            }
        }
    }
}
