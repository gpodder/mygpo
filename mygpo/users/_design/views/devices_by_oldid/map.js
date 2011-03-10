function(doc)
{
    if(doc.doc_type == "User")
    {
        for(n in doc.devices)
        {
            device = doc.devices[n];
            emit(device.oldid, device);
        }
    }
}
