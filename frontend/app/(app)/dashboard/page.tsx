"use client";
import { AppShell, PageContainer } from "@/components/layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, AlertTriangle, ShieldAlert, CheckCircle } from "lucide-react";
import { motion } from "framer-motion";

import { Variants } from "framer-motion";

const data = [
  { name: "Mon", incidents: 4, nearMisses: 12 },
  { name: "Tue", incidents: 3, nearMisses: 18 },
  { name: "Wed", incidents: 5, nearMisses: 15 },
  { name: "Thu", incidents: 2, nearMisses: 22 },
  { name: "Fri", incidents: 7, nearMisses: 10 },
  { name: "Sat", incidents: 1, nearMisses: 5 },
  { name: "Sun", incidents: 0, nearMisses: 8 },
];

const categories = [
  { name: "Slips/Trips", value: 45 },
  { name: "Equipment", value: 32 },
  { name: "Ergonomic", value: 28 },
  { name: "Vehicle", value: 15 },
  { name: "Chemical", value: 8 },
];

export default function DashboardPage() {
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <AppShell pageTitle="Dashboard">
      <PageContainer className="py-8 sm:py-10">
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="space-y-8"
        >
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-foreground">Overview</h2>
            <p className="text-muted-foreground mt-1">Your workspace safety signals at a glance.</p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <motion.div variants={itemVariants}>
              <Card className="glass-card border-none shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Signals</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">128</div>
                  <p className="text-xs text-muted-foreground mt-1">+14% from last month</p>
                </CardContent>
              </Card>
            </motion.div>
            
            <motion.div variants={itemVariants}>
              <Card className="glass-card border-none shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Incidents</CardTitle>
                  <AlertTriangle className="h-4 w-4 text-warning" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">22</div>
                  <p className="text-xs text-muted-foreground mt-1">-2% from last month</p>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div variants={itemVariants}>
              <Card className="glass-card border-none shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Near Misses</CardTitle>
                  <ShieldAlert className="h-4 w-4 text-primary" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">106</div>
                  <p className="text-xs text-muted-foreground mt-1">+18% from last month</p>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div variants={itemVariants}>
              <Card className="glass-card border-none shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Reviewed</CardTitle>
                  <CheckCircle className="h-4 w-4 text-success" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">94%</div>
                  <p className="text-xs text-muted-foreground mt-1">+4% from last month</p>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <motion.div variants={itemVariants} className="col-span-4">
              <Card className="glass-card border-none shadow-sm h-[400px] flex flex-col">
                <CardHeader>
                  <CardTitle>Safety Signals Over Time</CardTitle>
                  <CardDescription>Incidents and near misses for the past 7 days</CardDescription>
                </CardHeader>
                <CardContent className="flex-1 min-h-0 pl-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorIncidents" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#0f766e" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#0f766e" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorNearMisses" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#64748b" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#64748b" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                      <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                      <Area type="monotone" dataKey="nearMisses" stroke="#64748b" fillOpacity={1} fill="url(#colorNearMisses)" />
                      <Area type="monotone" dataKey="incidents" stroke="#0f766e" fillOpacity={1} fill="url(#colorIncidents)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </motion.div>
            
            <motion.div variants={itemVariants} className="col-span-3">
              <Card className="glass-card border-none shadow-sm h-[400px] flex flex-col">
                <CardHeader>
                  <CardTitle>Top Categories</CardTitle>
                  <CardDescription>Breakdown of reported signals by type</CardDescription>
                </CardHeader>
                <CardContent className="flex-1 min-h-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={categories} layout="vertical" margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                      <XAxis type="number" hide />
                      <YAxis dataKey="name" type="category" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip cursor={{fill: 'rgba(0,0,0,0.05)'}} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                      <Bar dataKey="value" fill="#0f766e" radius={[0, 4, 4, 0]} barSize={24} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </motion.div>
      </PageContainer>
    </AppShell>
  );
}
