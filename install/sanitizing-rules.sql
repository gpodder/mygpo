INSERT INTO `sanitizing_rules` VALUES (1,1,0,'feeds2\\.feedburner\\.com','feeds.feedburner.com',1,'Rewriting for feedburner should happen as \"feeds2.feedburner.com\" -> \"feeds.feedburner.com\"');
INSERT INTO `sanitizing_rules` VALUES (2,1,0,'(?P<unchanged>feedburner\\.com.+)\\?format=xml','\\g<unchanged>',2,'Feedburner URLs should have their \"?format=xml\" query string removed: \r\n\r\nhttp://feeds2.feedburner.com/linuxoutlaws?format=xml \r\nhttp://feeds.feedburner.com/linuxoutlaws \r\n');
INSERT INTO `sanitizing_rules` VALUES (3,1,0,'^\\s+','',0,'Remove leading whitespaces');
INSERT INTO `sanitizing_rules` VALUES (4,1,0,'\\s+$','',0,'Remove trailing whitespaces');
INSERT INTO `sanitizing_rules` VALUES (5,1,0,'^[^(https?):].+','',100,'Empty any string that doesn\'t start with either http or https');
INSERT INTO `sanitizing_rules` VALUES (6,1,0,'^https?://([0-9a-zA-z-\.]+\.)?gpodder.org.*','',100,'As gpodder.org doesn\'t host Podcasts, all URLs starting with this domain are considered invalid');
INSERT INTO `sanitizing_rules` VALUES (7,1,0,'(?P<unchanged>feedburner\\.com.+)\\/$','\\g<unchanged>',2,'Feedburner URLs sometimes have a trailing slash, which can be removed safely');

