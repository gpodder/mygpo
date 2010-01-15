INSERT INTO `sanitizing_rules` VALUES (1,1,0,'feeds2\\.feedburner\\.com','feeds.feedburner.com',1,'Rewriting for feedburner should happen as \"feeds2.feedburner.com\" -> \"feeds.feedburner.com\"');
INSERT INTO `sanitizing_rules` VALUES (2,1,0,'(?P<unchanged>feedburner\\.com.+)\\?format=xml','\\g<unchanged>',2,'Feedburner URLs should have their \"?format=xml\" query string removed: \r\n\r\nhttp://feeds2.feedburner.com/linuxoutlaws?format=xml \r\nhttp://feeds.feedburner.com/linuxoutlaws \r\n');

