/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.3-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: campaign_os
-- ------------------------------------------------------
-- Server version	11.8.3-MariaDB-0+deb13u1 from Debian

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `accounts_pagepermission`
--

DROP TABLE IF EXISTS `accounts_pagepermission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_pagepermission` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `role` varchar(20) NOT NULL,
  `page_id` varchar(50) NOT NULL,
  `can_access` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_pagepermission_role_page_id_6e68911d_uniq` (`role`,`page_id`),
  KEY `accounts_pagepermission_role_aaa367d8` (`role`),
  KEY `accounts_pagepermission_page_id_25c7c02c` (`page_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_role`
--

DROP TABLE IF EXISTS `accounts_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_role` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `accounts_role_created_at_b371308a` (`created_at`),
  KEY `accounts_role_is_active_30164ebb` (`is_active`),
  KEY `accounts_role_created_by_id_a5e8bbb3_fk_accounts_user_id` (`created_by_id`),
  KEY `accounts_role_updated_by_id_8a3f4e01_fk_accounts_user_id` (`updated_by_id`),
  CONSTRAINT `accounts_role_created_by_id_a5e8bbb3_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `accounts_role_updated_by_id_8a3f4e01_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_role_permissions`
--

DROP TABLE IF EXISTS `accounts_role_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_role_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `role_id` bigint(20) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_role_permissions_role_id_permission_id_032c715e_uniq` (`role_id`,`permission_id`),
  KEY `accounts_role_permis_permission_id_76fe677d_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_role_permis_permission_id_76fe677d_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `accounts_role_permissions_role_id_54f107a6_fk_accounts_role_id` FOREIGN KEY (`role_id`) REFERENCES `accounts_role` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_user`
--

DROP TABLE IF EXISTS `accounts_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `role` varchar(20) NOT NULL,
  `profile_photo` varchar(100) DEFAULT NULL,
  `bio` longtext DEFAULT NULL,
  `is_verified` tinyint(1) NOT NULL,
  `last_login_at` datetime(6) DEFAULT NULL,
  `booth_id` bigint(20) DEFAULT NULL,
  `constituency_id` bigint(20) DEFAULT NULL,
  `district_id` bigint(20) DEFAULT NULL,
  `state_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `phone` (`phone`),
  KEY `accounts_user_booth_id_b16778c6_fk_masters_booth_id` (`booth_id`),
  KEY `accounts_user_constituency_id_5621f0b8_fk_masters_c` (`constituency_id`),
  KEY `accounts_user_state_id_1a94d24f_fk_masters_state_id` (`state_id`),
  KEY `accounts_us_phone_f54457_idx` (`phone`),
  KEY `accounts_us_role_1fa9a5_idx` (`role`),
  KEY `accounts_us_distric_7a5152_idx` (`district_id`),
  CONSTRAINT `accounts_user_booth_id_b16778c6_fk_masters_booth_id` FOREIGN KEY (`booth_id`) REFERENCES `masters_booth` (`id`),
  CONSTRAINT `accounts_user_constituency_id_5621f0b8_fk_masters_c` FOREIGN KEY (`constituency_id`) REFERENCES `masters_constituency` (`id`),
  CONSTRAINT `accounts_user_district_id_29e32992_fk_masters_district_id` FOREIGN KEY (`district_id`) REFERENCES `masters_district` (`id`),
  CONSTRAINT `accounts_user_state_id_1a94d24f_fk_masters_state_id` FOREIGN KEY (`state_id`) REFERENCES `masters_state` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_user_groups`
--

DROP TABLE IF EXISTS `accounts_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_groups_user_id_group_id_59c0b32f_uniq` (`user_id`,`group_id`),
  KEY `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` (`group_id`),
  CONSTRAINT `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `accounts_user_groups_user_id_52b62117_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_user_user_permissions`
--

DROP TABLE IF EXISTS `accounts_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq` (`user_id`,`permission_id`),
  KEY `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `accounts_user_user_p_user_id_e4f0a161_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `accounts_userlog`
--

DROP TABLE IF EXISTS `accounts_userlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_userlog` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `action` varchar(100) NOT NULL,
  `resource_type` varchar(100) NOT NULL,
  `resource_id` bigint(20) DEFAULT NULL,
  `details` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`details`)),
  `ip_address` char(39) DEFAULT NULL,
  `user_agent` longtext NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_userlog_created_at_ce35ff02` (`created_at`),
  KEY `accounts_userlog_is_active_5491139f` (`is_active`),
  KEY `accounts_userlog_created_by_id_888fef30_fk_accounts_user_id` (`created_by_id`),
  KEY `accounts_userlog_updated_by_id_4cc41492_fk_accounts_user_id` (`updated_by_id`),
  KEY `accounts_us_user_id_1a90a5_idx` (`user_id`,`created_at`),
  KEY `accounts_us_action_ae06c9_idx` (`action`),
  CONSTRAINT `accounts_userlog_created_by_id_888fef30_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `accounts_userlog_updated_by_id_4cc41492_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `accounts_userlog_user_id_b8668504_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `activities_activitylog`
--

DROP TABLE IF EXISTS `activities_activitylog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `activities_activitylog` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `category` varchar(20) NOT NULL,
  `activity_type` varchar(100) NOT NULL,
  `date` date NOT NULL,
  `hours_worked` decimal(4,1) DEFAULT NULL,
  `village` varchar(200) NOT NULL,
  `booth_no` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `username` varchar(150) NOT NULL,
  `user_role` varchar(50) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `activities_activityl_created_by_id_126e354e_fk_accounts_` (`created_by_id`),
  KEY `activities_activityl_updated_by_id_f2eeb105_fk_accounts_` (`updated_by_id`),
  KEY `activities_activitylog_created_at_139ca726` (`created_at`),
  KEY `activities_activitylog_is_active_903d3635` (`is_active`),
  KEY `activities_activitylog_category_4b6f3189` (`category`),
  KEY `activities_activitylog_date_9f4cdd0b` (`date`),
  KEY `activities__categor_87e286_idx` (`category`,`date`),
  CONSTRAINT `activities_activityl_created_by_id_126e354e_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `activities_activityl_updated_by_id_f2eeb105_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `activities_fieldsurvey`
--

DROP TABLE IF EXISTS `activities_fieldsurvey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `activities_fieldsurvey` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `survey_date` date NOT NULL,
  `block` varchar(100) NOT NULL,
  `village` varchar(200) NOT NULL,
  `booth_no` varchar(20) NOT NULL,
  `voter_name` varchar(200) NOT NULL,
  `age` int(11) DEFAULT NULL,
  `gender` varchar(10) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `address` longtext NOT NULL,
  `is_registered` varchar(10) NOT NULL,
  `aware_of_candidate` varchar(10) NOT NULL,
  `likely_to_vote` varchar(10) NOT NULL,
  `support_level` varchar(50) NOT NULL,
  `party_preference` varchar(50) NOT NULL,
  `key_issues` longtext NOT NULL,
  `remarks` longtext NOT NULL,
  `surveyed_by` varchar(150) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `response_status` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `activities_fieldsurv_created_by_id_55156794_fk_accounts_` (`created_by_id`),
  KEY `activities_fieldsurv_updated_by_id_17bc9318_fk_accounts_` (`updated_by_id`),
  KEY `activities_fieldsurvey_created_at_681fae02` (`created_at`),
  KEY `activities_fieldsurvey_is_active_dd432d63` (`is_active`),
  KEY `activities_fieldsurvey_survey_date_50cc1040` (`survey_date`),
  KEY `activities__survey__8fec66_idx` (`survey_date`),
  KEY `activities__support_769e50_idx` (`support_level`),
  CONSTRAINT `activities_fieldsurv_created_by_id_55156794_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `activities_fieldsurv_updated_by_id_17bc9318_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `analytics_dashboardsnapshot`
--

DROP TABLE IF EXISTS `analytics_dashboardsnapshot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `analytics_dashboardsnapshot` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `snapshot_date` date NOT NULL,
  `total_voters` int(11) NOT NULL,
  `voters_contacted` int(11) NOT NULL,
  `voters_by_sentiment` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`voters_by_sentiment`)),
  `total_booths` int(11) NOT NULL,
  `booths_assigned` int(11) NOT NULL,
  `booths_working` int(11) NOT NULL,
  `total_volunteers` int(11) NOT NULL,
  `active_volunteers` int(11) NOT NULL,
  `avg_performance_score` double NOT NULL,
  `total_events` int(11) NOT NULL,
  `completed_events` int(11) NOT NULL,
  `total_attendees` int(11) NOT NULL,
  `surveys_conducted` int(11) NOT NULL,
  `feedback_received` int(11) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `analytics_dashboardsnapshot_snapshot_date_6186c3a7_uniq` (`snapshot_date`),
  KEY `analytics_dashboards_created_by_id_9a400483_fk_accounts_` (`created_by_id`),
  KEY `analytics_dashboards_updated_by_id_0a5d432a_fk_accounts_` (`updated_by_id`),
  KEY `analytics_dashboardsnapshot_created_at_f16124e9` (`created_at`),
  KEY `analytics_dashboardsnapshot_is_active_ddc7d598` (`is_active`),
  CONSTRAINT `analytics_dashboards_created_by_id_9a400483_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `analytics_dashboards_updated_by_id_0a5d432a_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `attendance_attendance`
--

DROP TABLE IF EXISTS `attendance_attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance_attendance` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `punch_in` datetime(6) NOT NULL,
  `punch_out` datetime(6) DEFAULT NULL,
  `attendance_date` date NOT NULL,
  `status` varchar(12) NOT NULL,
  `total_work_hours` decimal(5,2) NOT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `attendance_attendance_user_id_attendance_date_93ab6f7d_uniq` (`user_id`,`attendance_date`),
  KEY `attendance_attendance_attendance_date_42f4a712` (`attendance_date`),
  KEY `attendance_attendance_status_13b9a0c8` (`status`),
  KEY `attendance__user_id_a9ae8f_idx` (`user_id`,`attendance_date`),
  KEY `attendance__status_132c06_idx` (`status`),
  CONSTRAINT `attendance_attendance_user_id_2bd82a2c_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `campaigns_campaignevent`
--

DROP TABLE IF EXISTS `campaigns_campaignevent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `campaigns_campaignevent` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `event_type` varchar(50) NOT NULL,
  `scheduled_date` date NOT NULL,
  `scheduled_time` time(6) DEFAULT NULL,
  `location` varchar(300) NOT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `expected_attendees` int(11) NOT NULL,
  `actual_attendees` int(11) NOT NULL,
  `status` varchar(20) NOT NULL,
  `materials_prepared` longtext NOT NULL,
  `outcome_notes` longtext NOT NULL,
  `success_score` int(11) DEFAULT NULL,
  `constituency_id` bigint(20) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `organized_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `ward_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `campaigns_c_constit_8fe55f_idx` (`constituency_id`),
  KEY `campaigns_c_schedul_5eb5d6_idx` (`scheduled_date`),
  KEY `campaigns_c_status_0c39a3_idx` (`status`),
  KEY `campaigns_campaignev_created_by_id_7755844d_fk_accounts_` (`created_by_id`),
  KEY `campaigns_campaignev_organized_by_id_fefb7d7f_fk_accounts_` (`organized_by_id`),
  KEY `campaigns_campaignev_updated_by_id_0a1ab2c1_fk_accounts_` (`updated_by_id`),
  KEY `campaigns_campaignevent_ward_id_cb5a3163_fk_masters_ward_id` (`ward_id`),
  KEY `campaigns_campaignevent_created_at_9f4605a4` (`created_at`),
  KEY `campaigns_campaignevent_is_active_a3868963` (`is_active`),
  CONSTRAINT `campaigns_campaignev_constituency_id_92f9d33a_fk_masters_c` FOREIGN KEY (`constituency_id`) REFERENCES `masters_constituency` (`id`),
  CONSTRAINT `campaigns_campaignev_created_by_id_7755844d_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `campaigns_campaignev_organized_by_id_fefb7d7f_fk_accounts_` FOREIGN KEY (`organized_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `campaigns_campaignev_updated_by_id_0a1ab2c1_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `campaigns_campaignevent_ward_id_cb5a3163_fk_masters_ward_id` FOREIGN KEY (`ward_id`) REFERENCES `masters_ward` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `campaigns_eventattendee`
--

DROP TABLE IF EXISTS `campaigns_eventattendee`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `campaigns_eventattendee` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `attendee_type` varchar(20) NOT NULL,
  `name` varchar(200) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(254) NOT NULL,
  `feedback` longtext NOT NULL,
  `sentiment` varchar(20) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `event_id` bigint(20) NOT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `voter_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `campaigns_eventattendee_event_id_voter_id_c2f6c0e3_uniq` (`event_id`,`voter_id`),
  KEY `campaigns_eventatten_created_by_id_c012b8a5_fk_accounts_` (`created_by_id`),
  KEY `campaigns_eventatten_updated_by_id_8e08cfb2_fk_accounts_` (`updated_by_id`),
  KEY `campaigns_eventattendee_voter_id_f60f30ef_fk_voters_voter_id` (`voter_id`),
  KEY `campaigns_eventattendee_created_at_8f50ede9` (`created_at`),
  KEY `campaigns_eventattendee_is_active_620c8a38` (`is_active`),
  CONSTRAINT `campaigns_eventatten_created_by_id_c012b8a5_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `campaigns_eventatten_event_id_a51dbc2b_fk_campaigns` FOREIGN KEY (`event_id`) REFERENCES `campaigns_campaignevent` (`id`),
  CONSTRAINT `campaigns_eventatten_updated_by_id_8e08cfb2_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `campaigns_eventattendee_voter_id_f60f30ef_fk_voters_voter_id` FOREIGN KEY (`voter_id`) REFERENCES `voters_voter` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `campaigns_task`
--

DROP TABLE IF EXISTS `campaigns_task`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `campaigns_task` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `title` varchar(200) NOT NULL,
  `category` varchar(30) NOT NULL,
  `details` longtext NOT NULL,
  `expected_datetime` datetime(6) NOT NULL,
  `venue` varchar(300) NOT NULL,
  `qty` int(11) NOT NULL,
  `status` varchar(20) NOT NULL,
  `completed_datetime` datetime(6) DEFAULT NULL,
  `notes` longtext NOT NULL,
  `coordinator_id` bigint(20) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `delivery_incharge_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `campaigns_t_status_f66718_idx` (`status`),
  KEY `campaigns_t_expecte_04e810_idx` (`expected_datetime`),
  KEY `campaigns_task_coordinator_id_807c7e2e_fk_accounts_user_id` (`coordinator_id`),
  KEY `campaigns_task_created_by_id_eeaf41eb_fk_accounts_user_id` (`created_by_id`),
  KEY `campaigns_task_delivery_incharge_id_bea3c286_fk_accounts_user_id` (`delivery_incharge_id`),
  KEY `campaigns_task_updated_by_id_f01f332a_fk_accounts_user_id` (`updated_by_id`),
  KEY `campaigns_task_created_at_300a0506` (`created_at`),
  KEY `campaigns_task_is_active_2aa7c3b7` (`is_active`),
  CONSTRAINT `campaigns_task_coordinator_id_807c7e2e_fk_accounts_user_id` FOREIGN KEY (`coordinator_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `campaigns_task_created_by_id_eeaf41eb_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `campaigns_task_delivery_incharge_id_bea3c286_fk_accounts_user_id` FOREIGN KEY (`delivery_incharge_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `campaigns_task_updated_by_id_f01f332a_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `elections_election`
--

DROP TABLE IF EXISTS `elections_election`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `elections_election` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `election_type` varchar(20) NOT NULL,
  `announcement_date` date DEFAULT NULL,
  `nomination_start_date` date NOT NULL,
  `nomination_end_date` date NOT NULL,
  `election_date` date NOT NULL,
  `result_date` date DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `state_id` bigint(20) NOT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `elections_election_created_by_id_b34a6db3_fk_accounts_user_id` (`created_by_id`),
  KEY `elections_election_state_id_0d6dfd81_fk_masters_state_id` (`state_id`),
  KEY `elections_election_updated_by_id_192a803c_fk_accounts_user_id` (`updated_by_id`),
  KEY `elections_election_created_at_6e994049` (`created_at`),
  KEY `elections_election_is_active_2769435c` (`is_active`),
  CONSTRAINT `elections_election_created_by_id_b34a6db3_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `elections_election_state_id_0d6dfd81_fk_masters_state_id` FOREIGN KEY (`state_id`) REFERENCES `masters_state` (`id`),
  CONSTRAINT `elections_election_updated_by_id_192a803c_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `elections_poll`
--

DROP TABLE IF EXISTS `elections_poll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `elections_poll` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(200) NOT NULL,
  `sample_size` int(11) NOT NULL,
  `sampling_method` varchar(100) NOT NULL,
  `poll_date_start` date NOT NULL,
  `poll_date_end` date NOT NULL,
  `poll_results` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`poll_results`)),
  `accuracy_notes` longtext NOT NULL,
  `conducted_by_id` bigint(20) DEFAULT NULL,
  `constituency_id` bigint(20) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `election_id` bigint(20) NOT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `elections_poll_conducted_by_id_0c0658a7_fk_accounts_user_id` (`conducted_by_id`),
  KEY `elections_poll_constituency_id_5b9f1cc3_fk_masters_c` (`constituency_id`),
  KEY `elections_poll_created_by_id_ac736341_fk_accounts_user_id` (`created_by_id`),
  KEY `elections_poll_election_id_0c4b6c4b_fk_elections_election_id` (`election_id`),
  KEY `elections_poll_updated_by_id_f70e59ca_fk_accounts_user_id` (`updated_by_id`),
  KEY `elections_poll_created_at_b1431403` (`created_at`),
  KEY `elections_poll_is_active_2af137a8` (`is_active`),
  CONSTRAINT `elections_poll_conducted_by_id_0c0658a7_fk_accounts_user_id` FOREIGN KEY (`conducted_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `elections_poll_constituency_id_5b9f1cc3_fk_masters_c` FOREIGN KEY (`constituency_id`) REFERENCES `masters_constituency` (`id`),
  CONSTRAINT `elections_poll_created_by_id_ac736341_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `elections_poll_election_id_0c4b6c4b_fk_elections_election_id` FOREIGN KEY (`election_id`) REFERENCES `elections_election` (`id`),
  CONSTRAINT `elections_poll_updated_by_id_f70e59ca_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `elections_pollquestion`
--

DROP TABLE IF EXISTS `elections_pollquestion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `elections_pollquestion` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `question_text` varchar(500) NOT NULL,
  `question_type` varchar(20) NOT NULL,
  `order` int(11) NOT NULL,
  `options` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`options`)),
  `created_by_id` bigint(20) DEFAULT NULL,
  `poll_id` bigint(20) NOT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `elections_pollquesti_created_by_id_b51761fe_fk_accounts_` (`created_by_id`),
  KEY `elections_pollquestion_poll_id_47c6c478_fk_elections_poll_id` (`poll_id`),
  KEY `elections_pollquesti_updated_by_id_48477c58_fk_accounts_` (`updated_by_id`),
  KEY `elections_pollquestion_created_at_e4452210` (`created_at`),
  KEY `elections_pollquestion_is_active_e8de8102` (`is_active`),
  CONSTRAINT `elections_pollquesti_created_by_id_b51761fe_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `elections_pollquesti_updated_by_id_48477c58_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `elections_pollquestion_poll_id_47c6c478_fk_elections_poll_id` FOREIGN KEY (`poll_id`) REFERENCES `elections_poll` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `elections_pollresponse`
--

DROP TABLE IF EXISTS `elections_pollresponse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `elections_pollresponse` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `response_text` varchar(500) NOT NULL,
  `response_value` int(11) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `poll_id` bigint(20) NOT NULL,
  `question_id` bigint(20) NOT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `voter_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `elections_pollresponse_poll_id_question_id_vote_29380343_uniq` (`poll_id`,`question_id`,`voter_id`),
  KEY `elections_pollrespon_created_by_id_550ec8b3_fk_accounts_` (`created_by_id`),
  KEY `elections_pollrespon_question_id_c34016a4_fk_elections` (`question_id`),
  KEY `elections_pollrespon_updated_by_id_596ca959_fk_accounts_` (`updated_by_id`),
  KEY `elections_pollresponse_voter_id_8cd438fc_fk_voters_voter_id` (`voter_id`),
  KEY `elections_pollresponse_created_at_08eda740` (`created_at`),
  KEY `elections_pollresponse_is_active_8394e391` (`is_active`),
  CONSTRAINT `elections_pollrespon_created_by_id_550ec8b3_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `elections_pollrespon_question_id_c34016a4_fk_elections` FOREIGN KEY (`question_id`) REFERENCES `elections_pollquestion` (`id`),
  CONSTRAINT `elections_pollrespon_updated_by_id_596ca959_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `elections_pollresponse_poll_id_2c411267_fk_elections_poll_id` FOREIGN KEY (`poll_id`) REFERENCES `elections_poll` (`id`),
  CONSTRAINT `elections_pollresponse_voter_id_8cd438fc_fk_voters_voter_id` FOREIGN KEY (`voter_id`) REFERENCES `voters_voter` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_achievement`
--

DROP TABLE IF EXISTS `masters_achievement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_achievement` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `booth_id` bigint(20) DEFAULT NULL,
  `ward_id` bigint(20) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `masters_achievement_booth_id_17745ed9_fk_masters_booth_id` (`booth_id`),
  KEY `masters_achievement_ward_id_7c91b497_fk_masters_ward_id` (`ward_id`),
  KEY `masters_achievement_created_by_id_d32ca317_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_achievement_updated_by_id_d8317408_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_achievement_created_at_3ec26dcb` (`created_at`),
  KEY `masters_achievement_is_active_c329381d` (`is_active`),
  CONSTRAINT `masters_achievement_booth_id_17745ed9_fk_masters_booth_id` FOREIGN KEY (`booth_id`) REFERENCES `masters_booth` (`id`),
  CONSTRAINT `masters_achievement_created_by_id_d32ca317_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_achievement_updated_by_id_d8317408_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_achievement_ward_id_7c91b497_fk_masters_ward_id` FOREIGN KEY (`ward_id`) REFERENCES `masters_ward` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_booth`
--

DROP TABLE IF EXISTS `masters_booth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_booth` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` timestamp(6) NOT NULL,
  `updated_at` timestamp(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `number` varchar(10) NOT NULL,
  `name` varchar(200) NOT NULL,
  `code` varchar(5) NOT NULL,
  `address` longtext NOT NULL,
  `village` varchar(100) NOT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `total_voters` int(11) NOT NULL,
  `male_voters` int(11) NOT NULL,
  `female_voters` int(11) NOT NULL,
  `third_gender_voters` int(11) NOT NULL,
  `status` varchar(20) NOT NULL,
  `sentiment` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `primary_agent_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `ward_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `masters_booth_ward_id_number_58e0c13e_uniq` (`ward_id`,`number`),
  KEY `masters_boo_ward_id_dd6248_idx` (`ward_id`),
  KEY `masters_boo_status_99a563_idx` (`status`),
  KEY `masters_boo_latitud_f9a44d_idx` (`latitude`,`longitude`),
  KEY `masters_booth_created_by_id_3153cc6e_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_booth_primary_agent_id_33b331ea_fk_accounts_user_id` (`primary_agent_id`),
  KEY `masters_booth_updated_by_id_73062502_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_booth_created_at_84425e48` (`created_at`),
  KEY `masters_booth_is_active_86236b71` (`is_active`),
  CONSTRAINT `masters_booth_created_by_id_3153cc6e_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_booth_primary_agent_id_33b331ea_fk_accounts_user_id` FOREIGN KEY (`primary_agent_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_booth_updated_by_id_73062502_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_booth_ward_id_90a5f847_fk_masters_ward_id` FOREIGN KEY (`ward_id`) REFERENCES `masters_ward` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_booth_agents`
--

DROP TABLE IF EXISTS `masters_booth_agents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_booth_agents` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `booth_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `masters_booth_agents_booth_id_user_id_5cfaf7cd_uniq` (`booth_id`,`user_id`),
  KEY `masters_booth_agents_user_id_d9f6f339_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `masters_booth_agents_booth_id_a3f286de_fk_masters_booth_id` FOREIGN KEY (`booth_id`) REFERENCES `masters_booth` (`id`),
  CONSTRAINT `masters_booth_agents_user_id_d9f6f339_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_candidate`
--

DROP TABLE IF EXISTS `masters_candidate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_candidate` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(200) NOT NULL,
  `father_name` varchar(200) NOT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` varchar(1) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(254) NOT NULL,
  `address` longtext NOT NULL,
  `educational_qualification` varchar(200) NOT NULL,
  `professional_background` longtext NOT NULL,
  `photo` varchar(100) DEFAULT NULL,
  `bio` longtext NOT NULL,
  `is_incumbent` tinyint(1) NOT NULL,
  `election_symbol` varchar(100) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `constituency_id` bigint(20) NOT NULL,
  `party_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `masters_candidate_party_id_constituency_id_e912cd1e_uniq` (`party_id`,`constituency_id`),
  KEY `masters_can_constit_fba150_idx` (`constituency_id`),
  KEY `masters_can_party_i_c83ab5_idx` (`party_id`),
  KEY `masters_candidate_created_by_id_49792291_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_candidate_updated_by_id_790113ea_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_candidate_created_at_3f9a9911` (`created_at`),
  KEY `masters_candidate_is_active_5172590c` (`is_active`),
  CONSTRAINT `masters_candidate_constituency_id_1c0aa7e4_fk_masters_c` FOREIGN KEY (`constituency_id`) REFERENCES `masters_constituency` (`id`),
  CONSTRAINT `masters_candidate_created_by_id_49792291_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_candidate_party_id_8fcf7f1e_fk_masters_party_id` FOREIGN KEY (`party_id`) REFERENCES `masters_party` (`id`),
  CONSTRAINT `masters_candidate_updated_by_id_790113ea_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_constituency`
--

DROP TABLE IF EXISTS `masters_constituency`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_constituency` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `code` varchar(5) NOT NULL,
  `election_type` varchar(20) NOT NULL,
  `description` longtext NOT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `total_population` int(11) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `district_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `masters_constituency_district_id_code_a8788ecb_uniq` (`district_id`,`code`),
  KEY `masters_con_distric_4918df_idx` (`district_id`),
  KEY `masters_con_electio_f86ceb_idx` (`election_type`),
  KEY `masters_constituency_created_by_id_3014676b_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_constituency_updated_by_id_56d7e80c_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_constituency_created_at_d3f286dd` (`created_at`),
  KEY `masters_constituency_is_active_3122a01f` (`is_active`),
  CONSTRAINT `masters_constituency_created_by_id_3014676b_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_constituency_district_id_048eee18_fk_masters_district_id` FOREIGN KEY (`district_id`) REFERENCES `masters_district` (`id`),
  CONSTRAINT `masters_constituency_updated_by_id_56d7e80c_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_country`
--

DROP TABLE IF EXISTS `masters_country`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_country` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `code` varchar(3) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`),
  KEY `masters_country_created_by_id_2f41cb64_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_country_updated_by_id_0062321e_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_country_created_at_2598f92d` (`created_at`),
  KEY `masters_country_is_active_4088b740` (`is_active`),
  CONSTRAINT `masters_country_created_by_id_2f41cb64_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_country_updated_by_id_0062321e_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_district`
--

DROP TABLE IF EXISTS `masters_district`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_district` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `code` varchar(5) NOT NULL,
  `description` longtext NOT NULL,
  `office_address` longtext NOT NULL,
  `office_phone` varchar(20) NOT NULL,
  `office_email` varchar(254) NOT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `state_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `masters_district_state_id_code_0b4582fb_uniq` (`state_id`,`code`),
  KEY `masters_dis_state_i_025d22_idx` (`state_id`),
  KEY `masters_dis_name_e46181_idx` (`name`),
  KEY `masters_district_created_by_id_9ddbfc69_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_district_updated_by_id_cbb069c0_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_district_created_at_90f8a018` (`created_at`),
  KEY `masters_district_is_active_ce2d74a2` (`is_active`),
  CONSTRAINT `masters_district_created_by_id_9ddbfc69_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_district_state_id_606770e2_fk_masters_state_id` FOREIGN KEY (`state_id`) REFERENCES `masters_state` (`id`),
  CONSTRAINT `masters_district_updated_by_id_cbb069c0_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_issue`
--

DROP TABLE IF EXISTS `masters_issue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_issue` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `category` varchar(50) NOT NULL,
  `priority` int(11) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `masters_issue_created_by_id_d11b18f8_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_issue_updated_by_id_784a5864_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_issue_created_at_57fd8f0b` (`created_at`),
  KEY `masters_issue_is_active_3e2a428a` (`is_active`),
  CONSTRAINT `masters_issue_created_by_id_d11b18f8_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_issue_updated_by_id_784a5864_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_party`
--

DROP TABLE IF EXISTS `masters_party`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_party` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(200) NOT NULL,
  `code` varchar(5) NOT NULL,
  `description` longtext NOT NULL,
  `abbreviation` varchar(10) NOT NULL,
  `founded_year` int(11) DEFAULT NULL,
  `headquarters` varchar(200) NOT NULL,
  `president_name` varchar(200) NOT NULL,
  `primary_color` varchar(7) NOT NULL,
  `secondary_color` varchar(7) NOT NULL,
  `logo` varchar(100) DEFAULT NULL,
  `is_national` tinyint(1) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `abbreviation` (`abbreviation`),
  KEY `masters_party_created_by_id_89e6424d_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_party_updated_by_id_6dbfa75d_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_party_created_at_06a55eb1` (`created_at`),
  KEY `masters_party_is_active_f02a0daa` (`is_active`),
  CONSTRAINT `masters_party_created_by_id_89e6424d_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_party_updated_by_id_6dbfa75d_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_pollingarea`
--

DROP TABLE IF EXISTS `masters_pollingarea`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_pollingarea` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `code` varchar(10) NOT NULL,
  `description` longtext NOT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `constituency_id` bigint(20) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `masters_pollingarea_constituency_id_code_28cf5e15_uniq` (`constituency_id`,`code`),
  KEY `masters_pollingarea_created_by_id_daebdc6e_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_pollingarea_updated_by_id_8228c253_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_pollingarea_created_at_b457cc95` (`created_at`),
  KEY `masters_pollingarea_is_active_be9bbf8a` (`is_active`),
  CONSTRAINT `masters_pollingarea_constituency_id_7226f9d1_fk_masters_c` FOREIGN KEY (`constituency_id`) REFERENCES `masters_constituency` (`id`),
  CONSTRAINT `masters_pollingarea_created_by_id_daebdc6e_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_pollingarea_updated_by_id_8228c253_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_scheme`
--

DROP TABLE IF EXISTS `masters_scheme`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_scheme` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `scheme_type` varchar(100) NOT NULL,
  `launch_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `target_population` int(11) NOT NULL,
  `beneficiaries` int(11) NOT NULL,
  `budget` bigint(20) NOT NULL,
  `responsible_ministry` varchar(200) NOT NULL,
  `constituency_id` bigint(20) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `masters_sch_constit_30e497_idx` (`constituency_id`),
  KEY `masters_sch_scheme__33eff7_idx` (`scheme_type`),
  KEY `masters_scheme_created_by_id_8ad21277_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_scheme_updated_by_id_5f5d5044_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_scheme_created_at_f9a968c2` (`created_at`),
  KEY `masters_scheme_is_active_797e4033` (`is_active`),
  CONSTRAINT `masters_scheme_constituency_id_4bbe215b_fk_masters_c` FOREIGN KEY (`constituency_id`) REFERENCES `masters_constituency` (`id`),
  CONSTRAINT `masters_scheme_created_by_id_8ad21277_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_scheme_updated_by_id_5f5d5044_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_state`
--

DROP TABLE IF EXISTS `masters_state`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_state` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `code` varchar(3) NOT NULL,
  `country_id` bigint(20) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `masters_state_country_id_code_deb0ef48_uniq` (`country_id`,`code`),
  KEY `masters_sta_country_1e9887_idx` (`country_id`),
  KEY `masters_sta_name_c24f5a_idx` (`name`),
  KEY `masters_state_created_by_id_df21569e_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_state_updated_by_id_ef2a3758_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_state_created_at_eac81070` (`created_at`),
  KEY `masters_state_is_active_bd06e6f8` (`is_active`),
  CONSTRAINT `masters_state_country_id_9e90d66c_fk_masters_country_id` FOREIGN KEY (`country_id`) REFERENCES `masters_country` (`id`),
  CONSTRAINT `masters_state_created_by_id_df21569e_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_state_updated_by_id_ef2a3758_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `masters_ward`
--

DROP TABLE IF EXISTS `masters_ward`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `masters_ward` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `code` varchar(5) NOT NULL,
  `description` longtext NOT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `constituency_id` bigint(20) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `masters_ward_constituency_id_code_3801a12d_uniq` (`constituency_id`,`code`),
  KEY `masters_war_constit_fb08dd_idx` (`constituency_id`),
  KEY `masters_ward_created_by_id_d03c4538_fk_accounts_user_id` (`created_by_id`),
  KEY `masters_ward_updated_by_id_613f38d1_fk_accounts_user_id` (`updated_by_id`),
  KEY `masters_ward_created_at_014e0367` (`created_at`),
  KEY `masters_ward_is_active_0ca59e00` (`is_active`),
  CONSTRAINT `masters_ward_constituency_id_300c91e1_fk_masters_constituency_id` FOREIGN KEY (`constituency_id`) REFERENCES `masters_constituency` (`id`),
  CONSTRAINT `masters_ward_created_by_id_d03c4538_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `masters_ward_updated_by_id_613f38d1_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `polls_poll`
--

DROP TABLE IF EXISTS `polls_poll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `polls_poll` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `title` varchar(200) NOT NULL,
  `title_ta` varchar(200) NOT NULL,
  `constituency_name` varchar(200) NOT NULL,
  `constituency_no` int(11) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `starts_at` datetime(6) DEFAULT NULL,
  `ends_at` datetime(6) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `polls_poll_created_by_id_bba6b2dd_fk_accounts_user_id` (`created_by_id`),
  KEY `polls_poll_updated_by_id_a8579d96_fk_accounts_user_id` (`updated_by_id`),
  KEY `polls_poll_created_at_e5a13bf2` (`created_at`),
  KEY `polls_poll_is_active_fac22290` (`is_active`),
  CONSTRAINT `polls_poll_created_by_id_bba6b2dd_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `polls_poll_updated_by_id_a8579d96_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `polls_polloption`
--

DROP TABLE IF EXISTS `polls_polloption`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `polls_polloption` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `question_no` int(11) NOT NULL,
  `key` varchar(50) NOT NULL,
  `name` varchar(200) NOT NULL,
  `name_ta` varchar(200) NOT NULL,
  `sub_label` varchar(200) NOT NULL,
  `icon_bg` varchar(200) NOT NULL,
  `bar_color` varchar(20) NOT NULL,
  `is_winner` tinyint(1) NOT NULL,
  `display_order` int(11) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `poll_id` bigint(20) NOT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `polls_polloption_poll_id_question_no_key_10b9112c_uniq` (`poll_id`,`question_no`,`key`),
  KEY `polls_polloption_created_by_id_b58e761e_fk_accounts_user_id` (`created_by_id`),
  KEY `polls_polloption_updated_by_id_68b6ec2a_fk_accounts_user_id` (`updated_by_id`),
  KEY `polls_polloption_created_at_be3190dd` (`created_at`),
  KEY `polls_polloption_is_active_1eb44a97` (`is_active`),
  CONSTRAINT `polls_polloption_created_by_id_b58e761e_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `polls_polloption_poll_id_e1eaae7c_fk_polls_poll_id` FOREIGN KEY (`poll_id`) REFERENCES `polls_poll` (`id`),
  CONSTRAINT `polls_polloption_updated_by_id_68b6ec2a_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `polls_pollvote`
--

DROP TABLE IF EXISTS `polls_pollvote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `polls_pollvote` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `voter_ip` char(39) NOT NULL,
  `voted_at` datetime(6) NOT NULL,
  `poll_id` bigint(20) NOT NULL,
  `q1_option_id` bigint(20) DEFAULT NULL,
  `q2_option_id` bigint(20) DEFAULT NULL,
  `voter_user_id` bigint(20) DEFAULT NULL,
  `voter_name` varchar(200) NOT NULL,
  `voter_phone` varchar(20) NOT NULL,
  `voter_city` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `polls_pollvote_poll_id_voter_ip_5bb3084e_uniq` (`poll_id`,`voter_ip`),
  KEY `polls_pollvote_q1_option_id_883406eb_fk_polls_polloption_id` (`q1_option_id`),
  KEY `polls_pollvote_q2_option_id_a4fbcfe9_fk_polls_polloption_id` (`q2_option_id`),
  KEY `polls_pollvote_voter_user_id_6ba78ecc_fk_accounts_user_id` (`voter_user_id`),
  CONSTRAINT `polls_pollvote_poll_id_63786d1d_fk_polls_poll_id` FOREIGN KEY (`poll_id`) REFERENCES `polls_poll` (`id`),
  CONSTRAINT `polls_pollvote_q1_option_id_883406eb_fk_polls_polloption_id` FOREIGN KEY (`q1_option_id`) REFERENCES `polls_polloption` (`id`),
  CONSTRAINT `polls_pollvote_q2_option_id_a4fbcfe9_fk_polls_polloption_id` FOREIGN KEY (`q2_option_id`) REFERENCES `polls_polloption` (`id`),
  CONSTRAINT `polls_pollvote_voter_user_id_6ba78ecc_fk_accounts_user_id` FOREIGN KEY (`voter_user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `volunteers_volunteer`
--

DROP TABLE IF EXISTS `volunteers_volunteer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `volunteers_volunteer` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `experience_months` int(11) NOT NULL,
  `previous_campaigns` int(11) NOT NULL,
  `status` varchar(20) NOT NULL,
  `voters_contacted` int(11) NOT NULL,
  `events_attended` int(11) NOT NULL,
  `hours_contributed` int(11) NOT NULL,
  `performance_score` double NOT NULL,
  `booth_id` bigint(20) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  `ward_id` bigint(20) DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  `gender` varchar(20) NOT NULL,
  `joined_date` date DEFAULT NULL,
  `notes` longtext NOT NULL,
  `phone2` varchar(15) NOT NULL,
  `role` varchar(100) NOT NULL,
  `skills` varchar(300) NOT NULL,
  `source` varchar(100) NOT NULL,
  `vehicle` varchar(50) NOT NULL,
  `block` varchar(100) NOT NULL,
  `volunteer_type` varchar(30) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `volunteers__booth_i_69fdfc_idx` (`booth_id`),
  KEY `volunteers__status_6d3213_idx` (`status`),
  KEY `volunteers_volunteer_created_by_id_bed97c70_fk_accounts_user_id` (`created_by_id`),
  KEY `volunteers_volunteer_updated_by_id_8070799a_fk_accounts_user_id` (`updated_by_id`),
  KEY `volunteers_volunteer_ward_id_9d5eabf5_fk_masters_ward_id` (`ward_id`),
  KEY `volunteers_volunteer_created_at_0be4cf31` (`created_at`),
  KEY `volunteers_volunteer_is_active_266496ba` (`is_active`),
  CONSTRAINT `volunteers_volunteer_booth_id_41799095_fk_masters_booth_id` FOREIGN KEY (`booth_id`) REFERENCES `masters_booth` (`id`),
  CONSTRAINT `volunteers_volunteer_created_by_id_bed97c70_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `volunteers_volunteer_updated_by_id_8070799a_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `volunteers_volunteer_user_id_1b8ed0c2_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `volunteers_volunteer_ward_id_9d5eabf5_fk_masters_ward_id` FOREIGN KEY (`ward_id`) REFERENCES `masters_ward` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `volunteers_volunteerattendance`
--

DROP TABLE IF EXISTS `volunteers_volunteerattendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `volunteers_volunteerattendance` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date` date NOT NULL,
  `check_in_time` time(6) DEFAULT NULL,
  `check_out_time` time(6) DEFAULT NULL,
  `location` varchar(200) NOT NULL,
  `notes` longtext NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `volunteer_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `volunteers_volunteerattendance_volunteer_id_date_c03c2955_uniq` (`volunteer_id`,`date`),
  KEY `volunteers_volunteer_created_by_id_eb2785e3_fk_accounts_` (`created_by_id`),
  KEY `volunteers_volunteer_updated_by_id_22e76ce8_fk_accounts_` (`updated_by_id`),
  KEY `volunteers_volunteerattendance_created_at_78023c05` (`created_at`),
  KEY `volunteers_volunteerattendance_is_active_73766f59` (`is_active`),
  CONSTRAINT `volunteers_volunteer_created_by_id_eb2785e3_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `volunteers_volunteer_updated_by_id_22e76ce8_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `volunteers_volunteer_volunteer_id_4125618d_fk_volunteer` FOREIGN KEY (`volunteer_id`) REFERENCES `volunteers_volunteer` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `volunteers_volunteertask`
--

DROP TABLE IF EXISTS `volunteers_volunteertask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `volunteers_volunteertask` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `assignment_type` varchar(50) NOT NULL,
  `target_count` int(11) DEFAULT NULL,
  `due_date` date NOT NULL,
  `priority` int(11) NOT NULL,
  `status` varchar(20) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `actual_count` int(11) DEFAULT NULL,
  `completion_notes` longtext NOT NULL,
  `assigned_by_id` bigint(20) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `volunteer_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `volunteers_volunteer_assigned_by_id_1c4d73b2_fk_accounts_` (`assigned_by_id`),
  KEY `volunteers_volunteer_created_by_id_2d17e353_fk_accounts_` (`created_by_id`),
  KEY `volunteers_volunteer_updated_by_id_f74b46fd_fk_accounts_` (`updated_by_id`),
  KEY `volunteers_volunteer_volunteer_id_d11c1e69_fk_volunteer` (`volunteer_id`),
  KEY `volunteers_volunteertask_created_at_1c098372` (`created_at`),
  KEY `volunteers_volunteertask_is_active_08b0df69` (`is_active`),
  CONSTRAINT `volunteers_volunteer_assigned_by_id_1c4d73b2_fk_accounts_` FOREIGN KEY (`assigned_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `volunteers_volunteer_created_by_id_2d17e353_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `volunteers_volunteer_updated_by_id_f74b46fd_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `volunteers_volunteer_volunteer_id_d11c1e69_fk_volunteer` FOREIGN KEY (`volunteer_id`) REFERENCES `volunteers_volunteer` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voters_voter`
--

DROP TABLE IF EXISTS `voters_voter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `voters_voter` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `name` varchar(200) NOT NULL,
  `father_name` varchar(200) DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` varchar(10) NOT NULL,
  `voter_id` varchar(20) NOT NULL,
  `aadhaar` varchar(12) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `email` varchar(254) DEFAULT NULL,
  `address` longtext DEFAULT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `education_level` varchar(50) DEFAULT NULL,
  `occupation` varchar(100) DEFAULT NULL,
  `sentiment` varchar(20) DEFAULT NULL,
  `is_contacted` tinyint(1) DEFAULT NULL,
  `last_contacted_at` datetime(6) DEFAULT NULL,
  `contact_count` int(11) DEFAULT NULL,
  `has_attended_event` tinyint(1) DEFAULT NULL,
  `is_volunteer` tinyint(1) DEFAULT NULL,
  `feedback_score` int(11) DEFAULT NULL,
  `notes` longtext DEFAULT NULL,
  `booth_id` bigint(20) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `preferred_party_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `caste` varchar(100) DEFAULT NULL,
  `issue_name` varchar(200) DEFAULT NULL,
  `religion` varchar(50) DEFAULT NULL,
  `scheme_name` varchar(200) DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  `current_location` varchar(20) DEFAULT NULL,
  `sub_caste` varchar(100) DEFAULT NULL,
  `phone2` varchar(20) NOT NULL DEFAULT '',
  `village_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `voter_id` (`voter_id`),
  UNIQUE KEY `aadhaar` (`aadhaar`),
  KEY `voters_vote_booth_i_11ed6f_idx` (`booth_id`),
  KEY `voters_vote_voter_i_e862a5_idx` (`voter_id`),
  KEY `voters_vote_phone_177433_idx` (`phone`),
  KEY `voters_vote_sentime_d53c8b_idx` (`sentiment`),
  KEY `voters_vote_is_cont_9fb892_idx` (`is_contacted`),
  KEY `voters_voter_created_by_id_6e484170_fk_accounts_user_id` (`created_by_id`),
  KEY `voters_voter_preferred_party_id_29ab60c0_fk_masters_party_id` (`preferred_party_id`),
  KEY `voters_voter_updated_by_id_eff2aa20_fk_accounts_user_id` (`updated_by_id`),
  KEY `voters_voter_created_at_6a3e0ff6` (`created_at`),
  KEY `voters_voter_is_active_139d98d1` (`is_active`),
  KEY `voters_voter_phone_4a4eaddd` (`phone`),
  KEY `voters_voter_village_id_1adc4dd7_fk_masters_ward_id` (`village_id`),
  CONSTRAINT `voters_voter_booth_id_ab2f271a_fk_masters_booth_id` FOREIGN KEY (`booth_id`) REFERENCES `masters_booth` (`id`),
  CONSTRAINT `voters_voter_created_by_id_6e484170_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_voter_preferred_party_id_29ab60c0_fk_masters_party_id` FOREIGN KEY (`preferred_party_id`) REFERENCES `masters_party` (`id`),
  CONSTRAINT `voters_voter_updated_by_id_eff2aa20_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_voter_village_id_1adc4dd7_fk_masters_ward_id` FOREIGN KEY (`village_id`) REFERENCES `masters_ward` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voters_votercontact`
--

DROP TABLE IF EXISTS `voters_votercontact`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `voters_votercontact` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `method` varchar(20) NOT NULL,
  `duration_minutes` int(11) DEFAULT NULL,
  `notes` longtext NOT NULL,
  `sentiment_after` varchar(20) NOT NULL,
  `contacted_by_id` bigint(20) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `voter_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `voters_votercontact_contacted_by_id_a08935f5_fk_accounts_user_id` (`contacted_by_id`),
  KEY `voters_votercontact_created_by_id_01d52da7_fk_accounts_user_id` (`created_by_id`),
  KEY `voters_votercontact_updated_by_id_09cb843d_fk_accounts_user_id` (`updated_by_id`),
  KEY `voters_votercontact_voter_id_90c85ae3_fk_voters_voter_id` (`voter_id`),
  KEY `voters_votercontact_created_at_c3feb2e3` (`created_at`),
  KEY `voters_votercontact_is_active_7a69192e` (`is_active`),
  CONSTRAINT `voters_votercontact_contacted_by_id_a08935f5_fk_accounts_user_id` FOREIGN KEY (`contacted_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_votercontact_created_by_id_01d52da7_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_votercontact_updated_by_id_09cb843d_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_votercontact_voter_id_90c85ae3_fk_voters_voter_id` FOREIGN KEY (`voter_id`) REFERENCES `voters_voter` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voters_voterfeedback`
--

DROP TABLE IF EXISTS `voters_voterfeedback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `voters_voterfeedback` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `feedback_type` varchar(20) NOT NULL,
  `subject` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `status` varchar(20) NOT NULL,
  `resolution` longtext NOT NULL,
  `resolved_at` datetime(6) DEFAULT NULL,
  `assigned_to_id` bigint(20) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `issue_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `voter_id` bigint(20) DEFAULT NULL,
  `voter_name` varchar(200) NOT NULL,
  `voter_phone` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `voters_voterfeedback_assigned_to_id_d5094a8e_fk_accounts_user_id` (`assigned_to_id`),
  KEY `voters_voterfeedback_created_by_id_ed97c511_fk_accounts_user_id` (`created_by_id`),
  KEY `voters_voterfeedback_issue_id_98a426be_fk_masters_issue_id` (`issue_id`),
  KEY `voters_voterfeedback_updated_by_id_95dcd47a_fk_accounts_user_id` (`updated_by_id`),
  KEY `voters_voterfeedback_created_at_8527dea8` (`created_at`),
  KEY `voters_voterfeedback_is_active_c7adff6c` (`is_active`),
  KEY `voters_voterfeedback_voter_id_b7818491_fk_voters_voter_id` (`voter_id`),
  CONSTRAINT `voters_voterfeedback_assigned_to_id_d5094a8e_fk_accounts_user_id` FOREIGN KEY (`assigned_to_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_voterfeedback_created_by_id_ed97c511_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_voterfeedback_issue_id_98a426be_fk_masters_issue_id` FOREIGN KEY (`issue_id`) REFERENCES `masters_issue` (`id`),
  CONSTRAINT `voters_voterfeedback_updated_by_id_95dcd47a_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_voterfeedback_voter_id_b7818491_fk_voters_voter_id` FOREIGN KEY (`voter_id`) REFERENCES `voters_voter` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voters_voterpreference`
--

DROP TABLE IF EXISTS `voters_voterpreference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `voters_voterpreference` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `preferred_language` varchar(50) NOT NULL,
  `best_time_to_contact` varchar(50) NOT NULL,
  `do_not_contact` tinyint(1) NOT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `voter_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `voter_id` (`voter_id`),
  KEY `voters_voterpreferen_created_by_id_c242b135_fk_accounts_` (`created_by_id`),
  KEY `voters_voterpreferen_updated_by_id_5c2242a3_fk_accounts_` (`updated_by_id`),
  KEY `voters_voterpreference_created_at_28772139` (`created_at`),
  KEY `voters_voterpreference_is_active_e82e0f99` (`is_active`),
  CONSTRAINT `voters_voterpreferen_created_by_id_c242b135_fk_accounts_` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_voterpreferen_updated_by_id_5c2242a3_fk_accounts_` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_voterpreference_voter_id_bfdff8b5_fk_voters_voter_id` FOREIGN KEY (`voter_id`) REFERENCES `voters_voter` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voters_voterpreference_issues_of_interest`
--

DROP TABLE IF EXISTS `voters_voterpreference_issues_of_interest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `voters_voterpreference_issues_of_interest` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `voterpreference_id` bigint(20) NOT NULL,
  `issue_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `voters_voterpreference_i_voterpreference_id_issue_bda24d33_uniq` (`voterpreference_id`,`issue_id`),
  KEY `voters_voterpreferen_issue_id_5f2fd73e_fk_masters_i` (`issue_id`),
  CONSTRAINT `voters_voterpreferen_issue_id_5f2fd73e_fk_masters_i` FOREIGN KEY (`issue_id`) REFERENCES `masters_issue` (`id`),
  CONSTRAINT `voters_voterpreferen_voterpreference_id_4d776564_fk_voters_vo` FOREIGN KEY (`voterpreference_id`) REFERENCES `voters_voterpreference` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voters_votersurvey`
--

DROP TABLE IF EXISTS `voters_votersurvey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `voters_votersurvey` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `survey_type` varchar(50) NOT NULL,
  `responses` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`responses`)),
  `score` int(11) DEFAULT NULL,
  `created_by_id` bigint(20) DEFAULT NULL,
  `updated_by_id` bigint(20) DEFAULT NULL,
  `voter_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `voters_votersurvey_voter_id_survey_type_11b68f9c_uniq` (`voter_id`,`survey_type`),
  KEY `voters_votersurvey_created_by_id_f3793bee_fk_accounts_user_id` (`created_by_id`),
  KEY `voters_votersurvey_updated_by_id_ad80e7e7_fk_accounts_user_id` (`updated_by_id`),
  KEY `voters_votersurvey_created_at_cb5d7f63` (`created_at`),
  KEY `voters_votersurvey_is_active_1f9d9c73` (`is_active`),
  CONSTRAINT `voters_votersurvey_created_by_id_f3793bee_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_votersurvey_updated_by_id_ad80e7e7_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `voters_votersurvey_voter_id_3bbfec08_fk_voters_voter_id` FOREIGN KEY (`voter_id`) REFERENCES `voters_voter` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-03-25 11:16:45
