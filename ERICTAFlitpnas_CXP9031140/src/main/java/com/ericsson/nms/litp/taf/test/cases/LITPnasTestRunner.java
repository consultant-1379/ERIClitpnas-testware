package com.ericsson.nms.litp.taf.test.cases;

import java.util.List;
import java.util.Map;
import java.io.*;

import org.apache.log4j.Logger;
import org.testng.SkipException;
import org.testng.annotations.Test;

import com.ericsson.cifwk.taf.*;
import com.ericsson.cifwk.taf.annotations.*;
import com.ericsson.cifwk.taf.tools.cli.TimeoutException;

import com.ericsson.nms.litp.taf.operators.RPMUpgrade;
import com.ericsson.nms.litp.taf.operators.PythonTestRunner;
import com.ericsson.nms.litp.taf.operators.Error;

import javax.inject.Inject;


public class LITPnasTestRunner extends TorTestCaseHelper {
    
    Logger logger = Logger.getLogger(LITPnasTestRunner.class);

    @Inject
    private RPMUpgrade rpmUpgradeOperator;
    
    @Inject
    private PythonTestRunner pythonTestRunnerOperator;

    /**
     * @throws TimeoutException,FileNotFoundException
     * @DESCRIPTION Upgrade specific LITP rpm
     * @PRE Connection to SUT
     * @PRIORITY HIGH
     */

    @TestId(id = "CXP9031140-1", title = "Upgrade ERIClitpnas rpm on the MS")
    @Test(groups={"ACCEPTANCE"})
    public void upgradeERIClitpnasRPM() throws TimeoutException, FileNotFoundException {

        rpmUpgradeOperator.initialise("nas");

        assertEquals(0, rpmUpgradeOperator.upgradeRPM());
    }

    /**
     * @throws TimeoutException
     * @DESCRIPTION Run python test cases for ERIClitpcli package
     * @PRE Connection to SUT
     * @PRIORITY HIGH
     */
    @TestId(id = "CXP9031140-2", title = "Run python test cases for ERIClitpnas package")
    @Test(groups={"CDB_REGRESSION", "ACCEPTANCE"})
    public void runERIClitpnasTests() {

    	pythonTestRunnerOperator.initialise();



        assertEquals(0, pythonTestRunnerOperator.execute());
    }

    /**
     * @DESCRIPTION Verify that the Python xml reports can be consumed and reported
     * @PRE Execution of test {@link #runERIClitpnasTests()}
     * @PRIORITY HIGH
     * @param className
     * @param name
     * @param failures
     */
    @TestId(id = "CXP9031140-3", title = "Parse xml outputs from python tests")
    @DataDriven(name = "surefire-reports")
    @Test(groups={"ACCEPTANCE"})
    public void parseNosetestsReports(@Input("classname") String className, @Input("name") String name,
            @Input("failures") List<Map<String, String>> failures, @Input("errors") List<Map<String, String>> errors,
            @Input("skipped") List<Map<String, Object>> skipped){
        logger.debug("TestCase:");
        logger.debug("    classname:" + className);
        logger.debug("    name:" + name);
        setTestcase(className + ":" + name, "");
        setTestInfo(name);
        for (Map<String, String> failure : failures) {
            fail(failure.get("type") + failure.get("message") + failure.get("text"));
        }
        for (Map<String, String> error : errors) {
            throw new Error(error.get("type"), error.get("message"), error.get("text"));
        }
        for (Map<String, Object> skip : skipped) {
            int type = (int) skip.get("type");
            if(type > 0){
                throw new SkipException("Number of tests to be skipped is: " + type);
            }
        }
    }
} 
